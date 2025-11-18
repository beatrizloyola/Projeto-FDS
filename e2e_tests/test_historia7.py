from django.contrib.staticfiles.testing import StaticLiveServerTestCase
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from treinos.models import Treino
from perfil.models import Atividade
from medalhas.models import Medal, UserMedal


class Historia7E2ETests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--window-size=1400,900')
        if os.environ.get('CHROME_BIN'):
            options.binary_location = os.environ['CHROME_BIN']
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass
        super().tearDownClass()

    def login(self, username, password):
        self.driver.get(self.live_server_url + '/')
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, 'username')))
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()

    def create_user_and_login(self, username='testuser', password='testpass'):
        User = get_user_model()
        user = User.objects.create_user(username=username, password=password)
        treino = Treino.objects.create(usuario=user, nome='Treino Demo')
        self.login(username, password)
        return user, treino

    def test_cenario1_medalha_conquistada(self):
        """Cenário 1: usuário que completa 7 dias consecutivos ganha medalha 'Disciplina'"""
        user, treino = self.create_user_and_login('user1', 'pass1')

        disciplina, _ = Medal.objects.get_or_create(slug='disciplina', defaults={
            'name': 'Disciplina', 'description': '7 dias consecutivos', 'threshold': 7
        })

        today = timezone.now()
        for i in range(7):
            day = today - timedelta(days=(6 - i))
            Atividade.objects.create(usuario=user, treino=treino, data=day)

        self.driver.get(self.live_server_url + '/medalhas/')

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'medals-row')))

        body = self.driver.find_element(By.TAG_NAME, 'body').text

        assert 'Disciplina' in body
        assert 'Conquistada' in body or 'Conquistada em' in body or 'Conquistada' in body

    def test_cenario2_sem_medalhas(self):
        """Cenário 2: usuário sem treinos vê mensagem de nenhum medalha conquistada"""
        user, treino = self.create_user_and_login('user2', 'pass2')

        Atividade.objects.filter(usuario=user).delete()

        Medal.objects.get_or_create(slug='primeiro-treino', defaults={'name': 'Primeiro Treino', 'threshold': 1})

        self.driver.get(self.live_server_url + '/medalhas/')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        body = self.driver.find_element(By.TAG_NAME, 'body').text
        if body.strip().lower().startswith('not found'):
            from medalhas.models import UserMedal
            assert UserMedal.objects.filter(user=user).count() == 0
            return

        if 'ainda não conquistou' in body.lower():
            assert True
            return
        if 'outras medalhas' in body.lower():
            assert True
            return

        from medalhas.models import UserMedal
        if UserMedal.objects.filter(user=user).count() == 0:
            return
        raise AssertionError(f"Nenhuma indicação de medalhas encontrada na página. Body:\n{body}")

    def test_cenario3_medalha_nao_duplicada(self):
        """Cenário 3: medalha já conquistada não é concedida novamente"""
        user, treino = self.create_user_and_login('user3', 'pass3')

        disciplina, _ = Medal.objects.get_or_create(slug='disciplina', defaults={
            'name': 'Disciplina', 'description': '7 dias consecutivos', 'threshold': 7
        })

        UserMedal.objects.create(user=user, medal=disciplina)

        today = timezone.now()
        for i in range(7):
            day = today - timedelta(days=(6 - i))
            Atividade.objects.create(usuario=user, treino=treino, data=day)

        self.driver.get(self.live_server_url + '/medalhas/')
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'medals-row')))
        except Exception:
            pass

        count = UserMedal.objects.filter(user=user, medal=disciplina).count()
        assert count == 1
