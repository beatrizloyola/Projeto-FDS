import time
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from perfil.models import Perfil
from treinos.models import Treino

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class TestHistoria2Objetivo(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1280,900")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        cls.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options,
        )
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        finally:
            super().tearDownClass()

    def setUp(self):
        User = get_user_model()
        self.user, created = User.objects.get_or_create(
            username="e2e_user_obj",
            defaults={"email": "e2e_obj@example.com"},
        )
        if created or not self.user.has_usable_password():
            self.user.set_password("S3nh@Fort3!")
            self.user.save()

        self.perfil, _ = Perfil.objects.get_or_create(user=self.user)

        self.url_atividade = reverse('atividade')
        self.url_treinos = reverse('treinos')

    def _force_browser_login(self):
        client = Client()
        client.force_login(self.user)
        client.get(self.url_atividade)
        cookie_name = settings.SESSION_COOKIE_NAME
        sessionid = client.cookies[cookie_name].value
        csrftoken = client.cookies.get('csrftoken').value if client.cookies.get('csrftoken') else None

        self.driver.get(self.live_server_url + self.url_atividade)
        try:
            self.driver.execute_script("document.cookie = arguments[0]", f"{cookie_name}={sessionid}; path=/")
            if csrftoken:
                self.driver.execute_script("document.cookie = arguments[0]", f"csrftoken={csrftoken}; path=/")
        except Exception:
            parsed = urlparse(self.live_server_url)
            domain = parsed.hostname or "localhost"
            try:
                self.driver.add_cookie({"name": cookie_name, "value": sessionid, "path": "/", "domain": domain})
                if csrftoken:
                    self.driver.add_cookie({"name": "csrftoken", "value": csrftoken, "path": "/", "domain": domain})
            except Exception:
                pass

    def test_cenario_1_objetivo_definido_com_sucesso(self):
        """Cenário 1: Objetivo definido com sucesso"""
        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.objetivo-opcoes')))
        select_script = (
            "var v=arguments[0];"
            "var inputs=document.getElementsByName('objetivo');"
            "for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ var label = inputs[i].closest('.objetivo-item');"
            " if(label){ label.click(); } else { inputs[i].checked=true; inputs[i].dispatchEvent(new Event('change',{bubbles:true})); } return true; } } return false;"
        )
        ok = self.driver.execute_script(select_script, 'GANHO')
        selected = self.driver.execute_script("return (document.querySelector(\"input[name='objetivo']:checked\")||{}).value || null")
        if not ok or selected != 'GANHO':
            self.driver.execute_script("var v=arguments[0]; var inputs=document.getElementsByName('objetivo'); for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ var l=inputs[i].closest('.objetivo-item'); if(l) l.click(); } }", 'GANHO')
        try:
            self.driver.execute_script(
                "var v=arguments[0]; var inputs=document.getElementsByName('objetivo'); for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ inputs[i].checked=true; inputs[i].dispatchEvent(new Event('change',{bubbles:true})); } }; var f=document.querySelector('form'); if(f) f.submit();",
                'GANHO'
            )
        except Exception:
            save_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn-salvar'))
            )
            save_btn.click()

        WebDriverWait(self.driver, 10).until(EC.url_contains(self.url_atividade.strip('/')))

        perfil = Perfil.objects.get(user=self.user)
        self.assertEqual(perfil.objetivo, 'GANHO')

        exists_push = Treino.objects.filter(usuario=self.user, nome__icontains='Push').exists()
        self.assertTrue(exists_push, 'Esquema de treinos alinhado ao objetivo não foi criado')

    def test_cenario_2_objetivo_nao_salvo(self):
        """Cenário 2: Objetivo não salvo quando não clicar em Salvar"""
        self.perfil.objetivo = ''
        self.perfil.save()

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.objetivo-opcoes')))
        select_script = (
            "var v=arguments[0];"
            "var inputs=document.getElementsByName('objetivo');"
            "for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ var label = inputs[i].closest('.objetivo-item');"
            " if(label){ label.click(); } else { inputs[i].checked=true; inputs[i].dispatchEvent(new Event('change',{bubbles:true})); } return true; } } return false;"
        )
        ok = self.driver.execute_script(select_script, 'PERDA')
        selected = self.driver.execute_script("return (document.querySelector(\"input[name='objetivo']:checked\")||{}).value || null")
        if not ok or selected != 'PERDA':
            self.driver.execute_script("var v=arguments[0]; var inputs=document.getElementsByName('objetivo'); for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ var l=inputs[i].closest('.objetivo-item'); if(l) l.click(); } }", 'PERDA')

        self.driver.get(self.live_server_url + self.url_treinos)
        time.sleep(0.5)
        self.driver.get(self.live_server_url + self.url_atividade)

        perfil = Perfil.objects.get(user=self.user)
        self.assertEqual(perfil.objetivo, '', 'Objetivo não deveria ter sido salvo sem clicar em Salvar')

        has_scheme = Treino.objects.filter(usuario=self.user).filter(nome__icontains='Push').exists()
        self.assertFalse(has_scheme, 'Esquema não deveria ter sido criado sem salvar objetivo')

    def test_cenario_3_alteracao_objetivo_substitui_e_atualiza_plano(self):
        """Cenário 3: Alteração de objetivo substitui antigo e atualiza plano"""
        client = Client()
        client.force_login(self.user)
        client.post(self.url_atividade, {'acao': 'atualizar_objetivo', 'objetivo': 'GANHO'})

        perfil = Perfil.objects.get(user=self.user)
        self.assertEqual(perfil.objetivo, 'GANHO')
        self.assertTrue(Treino.objects.filter(usuario=self.user, nome__icontains='Push (Hipertrofia)').exists())

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.objetivo-opcoes')))
        select_script = (
            "var v=arguments[0];"
            "var inputs=document.getElementsByName('objetivo');"
            "for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ var label = inputs[i].closest('.objetivo-item');"
            " if(label){ label.click(); } else { inputs[i].checked=true; inputs[i].dispatchEvent(new Event('change',{bubbles:true})); } return true; } } return false;"
        )
        ok = self.driver.execute_script(select_script, 'PERDA')
        selected = self.driver.execute_script("return (document.querySelector(\"input[name='objetivo']:checked\")||{}).value || null")
        if not ok or selected != 'PERDA':
            self.driver.execute_script("var v=arguments[0]; var inputs=document.getElementsByName('objetivo'); for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ var l=inputs[i].closest('.objetivo-item'); if(l) l.click(); } }", 'PERDA')
        # Ensure radio input is checked and submit the form via JS
        try:
            self.driver.execute_script(
                "var v=arguments[0]; var inputs=document.getElementsByName('objetivo'); for(var i=0;i<inputs.length;i++){ if(inputs[i].value===v){ inputs[i].checked=true; inputs[i].dispatchEvent(new Event('change',{bubbles:true})); } }; var f=document.querySelector('form'); if(f) f.submit();",
                'PERDA'
            )
        except Exception:
            save_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn-salvar'))
            )
            save_btn.click()

        WebDriverWait(self.driver, 10).until(EC.url_contains(self.url_atividade.strip('/')))

        perfil = Perfil.objects.get(user=self.user)
        self.assertEqual(perfil.objetivo, 'PERDA')

        self.assertTrue(Treino.objects.filter(usuario=self.user, nome__icontains='Push (Perda de peso)').exists())
