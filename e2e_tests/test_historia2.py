from django.contrib.staticfiles.testing import StaticLiveServerTestCase
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

class Historia2E2ETests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--window-size=1200,900')
        if os.environ.get('CHROME_BIN'):
            options.binary_location = os.environ['CHROME_BIN']
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass
        super().tearDownClass()

    def create_and_login(self, username='notif_user', password='pass'):
        User = get_user_model()
        user = User.objects.create_user(username=username, password=password)
        from django.test import Client
        client = Client()
        client.force_login(user)

        self.driver.get(self.live_server_url + '/')

        if 'sessionid' in client.cookies:
            cookie_value = client.cookies['sessionid'].value
            self.driver.add_cookie({'name': 'sessionid', 'value': cookie_value, 'path': '/'})
            self.driver.get(self.live_server_url + '/')

        return user

    def inject_notification_stub(self, permission='granted'):
        script = f"""
        window.__notifs = [];
        window.Notification = function(title, opts) {{ window.__notifs.push({{title: title, opts: opts, ts: Date.now()}}); }};
        window.Notification.permission = '{permission}';
        window.Notification.requestPermission = function() {{ return Promise.resolve('{permission}'); }};
        """
        self.driver.execute_script(script)

    def set_notification_time_and_trigger(self, minutes_from_now):
        target = datetime.now() + timedelta(minutes=minutes_from_now)
        time_str = target.strftime('%H:%M')
        set_script = f"var inp=document.getElementById('notificacao-input'); if(inp){{ inp.value='{time_str}'; inp.dispatchEvent(new Event('change')); }}; return !!inp;"
        ok = self.driver.execute_script(set_script)
        return ok, time_str

    def wait_for_notification(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(lambda d: d.execute_script('return window.__notifs && window.__notifs.length > 0'))
            return True
        except Exception:
            return False

    def test_cenario1_notificacoes_ativadas(self):
        """Cenário 1: notificações ativadas -> notificação é enviada no tempo correto"""
        user = self.create_and_login('notif1', 'pass1')
        self.driver.get(self.live_server_url + '/perfil/usuario/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'notificacao-input')))

        self.inject_notification_stub(permission='granted')

        ok, ts = self.set_notification_time_and_trigger(minutes_from_now=1)
        assert ok, 'notification input not found'

        notified = self.wait_for_notification(timeout=70)
        assert notified, 'Expected a notification to be recorded but none occurred.'

    def test_cenario2_notificacoes_desativadas(self):
        """Cenário 2: notificações desativadas -> notificações não são enviadas"""
        user = self.create_and_login('notif2', 'pass2')
        self.driver.get(self.live_server_url + '/perfil/usuario/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'notificacao-input')))

        self.inject_notification_stub(permission='denied')

        ok, ts = self.set_notification_time_and_trigger(minutes_from_now=1)
        assert ok

        notified = self.wait_for_notification(timeout=40)
        assert not notified, 'Notification was recorded despite notifications being denied.'

    def test_cenario3_horario_alterado(self):
        """Cenário 3: alterar horário salva novo horário e notificações ocorrem no horário atualizado"""
        user = self.create_and_login('notif3', 'pass3')
        self.driver.get(self.live_server_url + '/perfil/usuario/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'notificacao-input')))

        self.inject_notification_stub(permission='granted')

        ok, t1 = self.set_notification_time_and_trigger(minutes_from_now=0.6)
        assert ok
        ok2, t2 = self.set_notification_time_and_trigger(minutes_from_now=1.6)
        assert ok2

        early = self.wait_for_notification(timeout=45)
        if early:
            notifs = self.driver.execute_script('return window.__notifs || [];')
            raise AssertionError(f'Notification fired before updated time: {notifs}')

        later = self.wait_for_notification(timeout=80)
        assert later, 'Expected notification at updated time but none occurred.'
