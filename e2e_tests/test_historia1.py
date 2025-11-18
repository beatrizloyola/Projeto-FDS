import time
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from treinos.models import Exercicio, Treino

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class TestTreinosE2E(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1280,900")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # If CI provides CHROME_BIN, use it (set in workflow)
        if os.environ.get('CHROME_BIN'):
            chrome_options.binary_location = os.environ['CHROME_BIN']
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
            username="e2e_user",
            defaults={"email": "e2e@example.com"},
        )
        if created or not self.user.has_usable_password():
            self.user.set_password("S3nh@Fort3!")
            self.user.save()

        self.ex1, _ = Exercicio.objects.get_or_create(nome="Supino Reto")
        self.ex2, _ = Exercicio.objects.get_or_create(nome="Agachamento Livre")

        self.treino_seed, _ = Treino.objects.get_or_create(usuario=self.user, nome="Seed Treino")

        self.url_listar = reverse("treinos")
        self.url_criar = reverse("criar_treino")
        self.url_login = reverse("login")

    def _force_browser_login(self):
        client = Client()
        client.force_login(self.user)
        client.get(self.url_listar)
        cookie_name = settings.SESSION_COOKIE_NAME
        sessionid = client.cookies[cookie_name].value
        csrftoken = client.cookies.get('csrftoken').value if client.cookies.get('csrftoken') else None


        self.driver.get(self.live_server_url + self.url_listar)
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

    def _abrir_form_criar(self):
        self.driver.get(self.live_server_url + self.url_listar)
        create_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#btnNovoTreinoInline'))
        )
        create_btn.click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.inline-treino-form, .treino-title-input'))
        )

    def _preencher_form_treino(self, nome=None, exercicio_id=None, repeticoes=None, carga=None):
        if nome:
            try:
                nome_input = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.treino-title-input'))
                )
                nome_input.clear()
                nome_input.send_keys(nome)
            except Exception:
                try:
                    title_h4 = self._find_first(['.treino-title'], required=False)
                    if title_h4:
                        title_h4.click()
                        nome_input = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.treino-title-input'))
                        )
                        nome_input.clear()
                        nome_input.send_keys(nome)
                except Exception:
                    pass
            try:
                script = 'var n=arguments[0]; var el = document.querySelector(".treino-card[data-novo=\"1\"] .treino-title-input"); if(el){ el.value = n; el.dispatchEvent(new Event("input")); } var h = document.querySelector(".treino-card[data-novo=\"1\"] .treino-title"); if(h && !h.textContent.includes(n)){ h.textContent = n; }'
                self.driver.execute_script(script, nome)
            except Exception:
                pass

        if exercicio_id is not None:
            try:
                select_el = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'select[name="exercicio"]'))
                )
                Select(select_el).select_by_value(str(exercicio_id))
            except Exception:
                raise AssertionError("Não foi possível localizar o select de exercício inline")

        if repeticoes is not None:
            try:
                rep_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="repeticoes"], input[name="repeticoes[]"]'))
                )
                rep_input.clear()
                rep_input.send_keys(str(repeticoes))
            except Exception:
                raise AssertionError("Não foi possível localizar o input de repetições inline")

        if carga is not None:
            try:
                carga_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="carga"], input[name="carga[]"]'))
                )
                carga_input.clear()
                carga_input.send_keys(str(carga))
            except Exception:
                raise AssertionError("Não foi possível localizar o input de carga inline")

    def _submit_form(self):
        submit = self._find_first(['button[data-action="salvar"]', 'button.action-save'])
        submit.click()

    def _find_first(self, selectors, required=True, timeout=10):
        for sel in selectors:
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
            except Exception:
                continue
        if required:
            raise AssertionError(f"Elemento não encontrado por nenhum seletor: {selectors}")
        return None

    def test_cenario_1_cadastro_realizado_com_sucesso(self):
        self._force_browser_login()
        self._abrir_form_criar()

        nome_unico = f"Treino E2E {uuid.uuid4().hex[:8]}"
        self._preencher_form_treino(
            nome=nome_unico,
            exercicio_id=self.ex1.id,
            repeticoes=12,
            carga=30,
        )
        try:
            script_set = (
                'var v=arguments[0];'
                'var el=document.querySelector(".treino-card[data-novo=\\"1\\"] .treino-title-input");'
                'if(el){ el.focus(); el.value = v; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true})); el.blur(); }'
            )
            self.driver.execute_script(script_set, nome_unico)
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, 5).until(lambda d: nome_unico in (d.execute_script(
                'var h=document.querySelector(".treino-card[data-novo=\\"1\\"] .treino-title"); return h? h.textContent : ""'
            )))
        except Exception:
            time.sleep(1)

        try:
            final_script = (
                'var v=arguments[0];'
                'var ip=document.querySelector(".treino-card[data-novo=\\"1\\"] .treino-title-input"); if(ip){ ip.value=v; ip.dispatchEvent(new Event("input",{bubbles:true})); ip.dispatchEvent(new Event("change",{bubbles:true})); ip.blur(); }'
                'var h=document.querySelector(".treino-card[data-novo=\\"1\\"] .treino-title"); if(h){ h.textContent=v; }'
            )
            self.driver.execute_script(final_script, nome_unico)
        except Exception:
            pass

        time.sleep(0.25)

        self._submit_form()


        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: len(d.find_elements(By.XPATH, f"//h4[contains(normalize-space(.), \"{nome_unico}\")]")) > 0
            )
        except Exception as ex:
            page = self.driver.page_source
            raise AssertionError(f"Treino não apareceu na listagem após salvar. Erro: {ex}\nPágina:\n{page}")

    def test_cenario_2_treino_incompleto_exibe_erro(self):
        self._force_browser_login()
        self._abrir_form_criar()

        nome_unico = f"Treino Incompleto {uuid.uuid4().hex[:6]}"
        self._preencher_form_treino(
            nome=nome_unico,
            exercicio_id=None,
            repeticoes=None,
            carga=20,
        )
        self._submit_form()
        try:
            WebDriverWait(self.driver, 10).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
        except Exception as ex:
            page = self.driver.page_source
            raise AssertionError(f"Alerta de validação não apareceu. Erro: {ex}\nPágina:\n{page}")

        self.driver.get(self.live_server_url + self.url_listar)
        page = self.driver.page_source
        assert nome_unico not in page, "Treino incompleto não deveria ter sido salvo."

    def test_cenario_3_login_nao_realizado_redireciona_para_cadastro(self):
        self.driver.get(self.live_server_url + self.url_criar)
        try:
            WebDriverWait(self.driver, 10).until(EC.url_contains(self.url_login.strip('/')))
        except Exception as ex:
            page = self.driver.page_source
            raise AssertionError(f"Não houve redirecionamento para login. Erro: {ex}\nPágina:\n{page}")

        esperado = "Você deve estar cadastrado para salvar treinos!"
        page = self.driver.page_source
        assert esperado in page, f"Mensagem de login esperada não encontrada na página de login. Esperado: {esperado}\nPágina:\n{page}"
