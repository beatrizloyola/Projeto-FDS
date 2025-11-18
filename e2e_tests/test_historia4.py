import time
from urllib.parse import urlparse
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from perfil.models import Perfil, Atividade
from treinos.models import Treino, TreinoExercicio, Exercicio

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class TestHistoria4VisualizarAtividade(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1280,900")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if os.environ.get('CHROME_BIN'):
            chrome_options.binary_location = os.environ['CHROME_BIN']
        from .driver_factory import create_driver
        cls.driver = create_driver(chrome_options)
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
            username="e2e_user_h4",
            defaults={"email": "e2e_h4@example.com"},
        )
        if created or not self.user.has_usable_password():
            self.user.set_password("S3nh@Fort3!")
            self.user.save()

        self.perfil, _ = Perfil.objects.get_or_create(user=self.user)

        self.url_treinos = reverse('treinos')
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

    def _create_simple_treino(self, nome="Treino E2E"):
        ex, _ = Exercicio.objects.get_or_create(nome="Exercicio E2E")
        treino = Treino.objects.create(usuario=self.user, nome=nome)
        TreinoExercicio.objects.create(treino=treino, exercicio=ex, carga=1, repeticoes=10, descanso=60)
        return treino

    def test_cenario_1_treino_cadastrado_mostra_atividade(self):
        """Cenário 1: Treino cadastrado e confirmado aparece no gráfico"""
        treino = self._create_simple_treino('H4 Treino 1')

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_treinos)

        card = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".treino-card[data-treino-id=\"{treino.id}\"]")))
        finish = card.find_element(By.CSS_SELECTOR, 'button.finish-box')
        finish.click()
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.notificacao-topo')))
        except Exception:
            time.sleep(0.2)

        self.driver.get(self.live_server_url + self.url_atividade)
        self.wait.until(EC.presence_of_element_located((By.ID, 'graficoTreinos')))
        labels = self.driver.execute_script('return window.__GRAFICO__ && window.__GRAFICO__.mensalLabels ? window.__GRAFICO__.mensalLabels : []')
        values = self.driver.execute_script('return window.__GRAFICO__ && window.__GRAFICO__.mensalValues ? window.__GRAFICO__.mensalValues : []')
        self.assertTrue(isinstance(values, list))
        self.assertTrue(any(v for v in values), 'Chart values should contain at least one non-zero entry after confirming a treino')

    def test_cenario_2_sem_treinos_confirmados_mostra_grafico_vazio(self):
        """Cenário 2: sem treinos confirmados, gráfico vazio"""
        Atividade.objects.filter(usuario=self.user).delete()

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        self.wait.until(EC.presence_of_element_located((By.ID, 'graficoTreinos')))
        values = self.driver.execute_script('return window.__GRAFICO__ && window.__GRAFICO__.mensalValues ? window.__GRAFICO__.mensalValues : []')
        if values:
            self.assertFalse(any(v for v in values), 'Chart should be empty when no treinos confirmed')

    def test_cenario_3_alterar_faixa_de_tempo_atualiza_dinamicamente(self):
        """Cenário 3: trocar faixa entre anual e mensal atualiza o gráfico sem reload"""
        treino = self._create_simple_treino('H4 Treino 2')
        client = Client()
        client.force_login(self.user)
        client.post(reverse('concluir_treino', args=(treino.id,)), {})

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        self.wait.until(EC.presence_of_element_located((By.ID, 'graficoTreinos')))
        mensal_values = self.driver.execute_script('return window.__GRAFICO__.mensalValues')
        anual_values = self.driver.execute_script('return window.__GRAFICO__.anualValues')

        anual_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.tab-btn[data-chart="anual"]')))
        anual_btn.click()
        time.sleep(0.2)
        self.assertTrue('ativo' in anual_btn.get_attribute('class'))

        mensal_btn = self.driver.find_element(By.CSS_SELECTOR, '.tab-btn[data-chart="mensal"]')
        mensal_btn.click()
        time.sleep(0.2)
        self.assertTrue('ativo' in mensal_btn.get_attribute('class'))
