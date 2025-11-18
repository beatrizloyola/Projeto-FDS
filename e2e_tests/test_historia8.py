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


class TestHistoria8MetaPerda(StaticLiveServerTestCase):
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
            username="e2e_user_h8",
            defaults={"email": "e2e_h8@example.com"},
        )
        if created or not self.user.has_usable_password():
            self.user.set_password("S3nh@Fort3!")
            self.user.save()

        self.perfil, _ = Perfil.objects.get_or_create(user=self.user)

        self.url_treinos = reverse('treinos')

    def _force_browser_login(self):
        client = Client()
        client.force_login(self.user)
        client.get(self.url_treinos)
        cookie_name = settings.SESSION_COOKIE_NAME
        sessionid = client.cookies[cookie_name].value
        csrftoken = client.cookies.get('csrftoken').value if client.cookies.get('csrftoken') else None

        self.driver.get(self.live_server_url + self.url_treinos)
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

    def _create_treino_with_gasto(self, nome, gasto):
        ex, _ = Exercicio.objects.get_or_create(nome=f"Ex {nome}")
        ex.gasto_kcal_por_hora = gasto
        ex.save()
        treino = Treino.objects.create(usuario=self.user, nome=nome)
        TreinoExercicio.objects.create(treino=treino, exercicio=ex, carga=1, repeticoes=10, descanso=60)
        return treino

    def test_cenario_1_meta_definida_e_treino_confirmado(self):
        """Cenário 1: Meta definida e treino confirmado mostra calorias e progresso"""

        from django.utils import timezone
        self.perfil.meta_calorias = 875 
        self.perfil.meta_set_at = timezone.now() - timezone.timedelta(days=1)
        self.perfil.save()

        treino = self._create_treino_with_gasto('H8 A', 350)

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_treinos)

        card = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".treino-card[data-treino-id=\"{treino.id}\"]")))
        finish = card.find_element(By.CSS_SELECTOR, 'button.finish-box')
        finish.click()

        note = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.notificacao-topo .notificacao-conteudo')))
        text = note.text
        self.assertIn('kcal', text)
        self.assertIn('atingiu 40%', text)

    def test_cenario_2_meta_nao_definida(self):
        """Cenário 2: Sem meta definida, apenas mostra calorias estimadas"""
        self.perfil.meta_calorias = None
        self.perfil.meta_set_at = None
        self.perfil.save()

        treino = self._create_treino_with_gasto('H8 B', 300)

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_treinos)

        card = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".treino-card[data-treino-id=\"{treino.id}\"]")))
        finish = card.find_element(By.CSS_SELECTOR, 'button.finish-box')
        finish.click()

        note = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.notificacao-topo .notificacao-conteudo')))
        text = note.text
        self.assertIn('kcal', text)
        self.assertNotIn('atingiu', text)
        self.assertNotIn('meta atingida', text)

    def test_cenario_3_meta_atingida(self):
        """Cenário 3: Confirma treino que atinge/ultrapassa a meta e mostra conclusão"""
        from django.utils import timezone
        self.perfil.meta_calorias = 400
        self.perfil.meta_set_at = timezone.now() - timezone.timedelta(days=7)
        self.perfil.save()

        prior_treino = Treino.objects.create(usuario=self.user, nome='Prior H8')
        Atividade.objects.create(usuario=self.user, treino=prior_treino, calorias_gastas=300)

        treino = self._create_treino_with_gasto('H8 C', 150)

        self._force_browser_login()
        self.driver.get(self.live_server_url + self.url_treinos)

        card = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".treino-card[data-treino-id=\"{treino.id}\"]")))
        finish = card.find_element(By.CSS_SELECTOR, 'button.finish-box')
        finish.click()

        note = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.notificacao-topo .notificacao-conteudo')))
        text = note.text
        self.assertIn('meta atingida', text)
        self.assertIn('kcal', text)
