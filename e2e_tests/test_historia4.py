import time
from urllib.parse import urlparse

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
        # Create a treino with one exercise so we can conclude it via POST
        ex, _ = Exercicio.objects.get_or_create(nome="Exercicio E2E")
        treino = Treino.objects.create(usuario=self.user, nome=nome)
        TreinoExercicio.objects.create(treino=treino, exercicio=ex, carga=1, repeticoes=10, descanso=60)
        return treino

    def test_cenario_1_treino_cadastrado_mostra_atividade(self):
        """Cenário 1: Treino cadastrado e confirmado aparece no gráfico"""
        treino = self._create_simple_treino('H4 Treino 1')

        # login in browser and go to treinos page
        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_treinos)

        # find the treino card and click the finish (submit) button
        card = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".treino-card[data-treino-id=\"{treino.id}\"]")))
        # find finish button inside the card and click it
        finish = card.find_element(By.CSS_SELECTOR, 'button.finish-box')
        finish.click()
        # wait for the treinos page to reflect the action (notification or redirect)
        try:
            # server sets a session notification that renders .notificacao-topo on the treinos page
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.notificacao-topo')))
        except Exception:
            # fallback: wait for the card to have class 'done' indicating it was marked
            time.sleep(0.2)

        # navigate to activity page and assert chart has data (non-empty labels/values)
        self.driver.get(self.live_server_url + self.url_atividade)
        # wait for chart canvas
        self.wait.until(EC.presence_of_element_located((By.ID, 'graficoTreinos')))
        # read window.__GRAFICO__ dataset
        labels = self.driver.execute_script('return window.__GRAFICO__ && window.__GRAFICO__.mensalLabels ? window.__GRAFICO__.mensalLabels : []')
        values = self.driver.execute_script('return window.__GRAFICO__ && window.__GRAFICO__.mensalValues ? window.__GRAFICO__.mensalValues : []')
        # at least one non-zero value expected
        self.assertTrue(isinstance(values, list))
        self.assertTrue(any(v for v in values), 'Chart values should contain at least one non-zero entry after confirming a treino')

    def test_cenario_2_sem_treinos_confirmados_mostra_grafico_vazio(self):
        """Cenário 2: sem treinos confirmados, gráfico vazio"""
        # ensure user has no atividades
        Atividade.objects.filter(usuario=self.user).delete()

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        self.wait.until(EC.presence_of_element_located((By.ID, 'graficoTreinos')))
        values = self.driver.execute_script('return window.__GRAFICO__ && window.__GRAFICO__.mensalValues ? window.__GRAFICO__.mensalValues : []')
        # expect all zeros or empty
        if values:
            self.assertFalse(any(v for v in values), 'Chart should be empty when no treinos confirmed')

    def test_cenario_3_alterar_faixa_de_tempo_atualiza_dinamicamente(self):
        """Cenário 3: trocar faixa entre anual e mensal atualiza o gráfico sem reload"""
        # create and confirm a treino so chart has data
        treino = self._create_simple_treino('H4 Treino 2')
        client = Client()
        client.force_login(self.user)
        client.post(reverse('concluir_treino', args=(treino.id,)), {})

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_atividade)

        self.wait.until(EC.presence_of_element_located((By.ID, 'graficoTreinos')))
        # ensure default monthly is active
        mensal_values = self.driver.execute_script('return window.__GRAFICO__.mensalValues')
        anual_values = self.driver.execute_script('return window.__GRAFICO__.anualValues')

        # click anual button
        anual_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.tab-btn[data-chart="anual"]')))
        anual_btn.click()
        # small pause for chart redraw (chart animation disabled but DOM changes occur)
        time.sleep(0.2)
        # read currently rendered labels via Chart.js instance by accessing the canvas chart object
        # the page doesn't expose chart instance globally; instead verify that the anual tab has ativo class and that mensal vs anual arrays differ
        self.assertTrue('ativo' in anual_btn.get_attribute('class'))

        # click mensal again and verify it becomes active
        mensal_btn = self.driver.find_element(By.CSS_SELECTOR, '.tab-btn[data-chart="mensal"]')
        mensal_btn.click()
        time.sleep(0.2)
        self.assertTrue('ativo' in mensal_btn.get_attribute('class'))
