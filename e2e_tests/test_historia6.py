import time
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from perfil.models import Perfil, Atividade

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class TestHistoria6IMC(StaticLiveServerTestCase):
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
            username="e2e_user_h6",
            defaults={"email": "e2e_h6@example.com"},
        )
        if created or not self.user.has_usable_password():
            self.user.set_password("S3nh@Fort3!")
            self.user.save()

        self.perfil, _ = Perfil.objects.get_or_create(user=self.user)

        self.url_atividade = reverse('atividade')

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

    def test_cenario_1_calculos_realizados_com_sucesso(self):
        """Cenário 1: cálculos realizados com sucesso e resultados exibidos"""
        self.perfil.altura_m = None
        self.perfil.peso_kg = None
        self.perfil.save()

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        editar_url = reverse('editar_usuario')
        self.driver.get(self.live_server_url + editar_url)

        altura_input = self.wait.until(EC.presence_of_element_located((By.NAME, 'altura')))
        peso_input = self.driver.find_element(By.NAME, 'peso')
        first_input = self.driver.find_element(By.NAME, 'first_name')
        last_input = self.driver.find_element(By.NAME, 'last_name')

        first_input.clear(); first_input.send_keys('E2E')
        last_input.clear(); last_input.send_keys('User')
        altura_input.clear(); altura_input.send_keys('150')
        peso_input.clear(); peso_input.send_keys('50')

        salvar = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        salvar.click()

        saved = False
        for _ in range(20):
            p = Perfil.objects.get(user=self.user)
            if p.peso_kg is not None and p.altura_m is not None:
                saved = True
                break
            time.sleep(0.2)
        if not saved:
            raise AssertionError('Perfil was not persisted with altura/peso after submitting the edit form')

        self.driver.get(self.live_server_url + self.url_atividade)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.imc-resultado')))

        resultado_text = self.driver.find_element(By.CSS_SELECTOR, '.imc-resultado').text
        self.assertIn('Resultado', resultado_text)
        self.assertTrue('Peso normal' in resultado_text or 'Resultado' in resultado_text)

        self.assertIn('Gasto calórico diário médio', resultado_text)
        self.assertIn('Consumo de água recomendado', resultado_text)

    def test_cenario_2_dados_insuficientes_para_calculo(self):
        """Cenário 2: dados insuficientes => não calcula e mostra mensagem"""
        self.perfil.altura_m = None
        self.perfil.peso_kg = None
        self.perfil.save()

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        body = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
        self.assertIn('Por favor, complete seus dados de altura e peso no perfil.', body)
        self.assertNotIn('Resultado:', body)

    def test_cenario_3_dados_invalidos_para_calculo(self):
        """Cenário 3: dados inválidos não permitem cálculo e mostram mensagem de erro"""
        self._force_browser_login()
        editar_url = reverse('editar_usuario')
        self.driver.get(self.live_server_url + editar_url)

        altura_input = self.wait.until(EC.presence_of_element_located((By.NAME, 'altura')))
        peso_input = self.driver.find_element(By.NAME, 'peso')

        altura_input.clear(); altura_input.send_keys('0')
        peso_input.clear(); peso_input.send_keys('abc')

        salvar = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        salvar.click()

        body_text = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
        self.assertIn('Os valores são inválidos. Por favor, revise os campos e tente novamente.', body_text)
