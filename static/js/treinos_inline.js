/* Treinos Inline - Fase 1
 * Objetivo: transformar cards vazios ou recém-criados em modo de edição inline sem redirecionar.
 */
(function(){
  const board = document.getElementById('treinosBoard');
  if(!board) return;
  const createBtn = document.getElementById('btnNovoTreinoInline');
  const criarTreinoUrl = board.getAttribute('data-exercicios-url') || '/treinos/criar/';

  // Helper para criar bloco de exercício
  function createExerciseBlock(exerciciosOptionsHtml){
    const wrapper = document.createElement('div');
    wrapper.className = 'exercise-form inline-edit';
    wrapper.innerHTML = `
      <div style="font-size:12px; font-weight:600;">Novo Exercício</div>
      <select name="exercicio" required>${exerciciosOptionsHtml}</select>
      <input type="number" name="carga" placeholder="Carga (kg)">
      <input type="number" name="repeticoes" placeholder="Repetições">
      <input type="number" name="descanso" placeholder="Descanso (s)">
      <div class="exercise-actions">
        <button type="button" class="btn-salvar-ex" data-action="add-more">+ Outro</button>
        <button type="button" class="btn-salvar-ex" data-action="remove" style="background:#822;">Remover</button>
      </div>`;
    return wrapper;
  }

  // Montar options a partir de script injection (template server-side)
  const exerciciosSelectTemplate = (function(){
    const scriptTemplate = document.getElementById('exercicios-options-template');
    if(scriptTemplate){
      return scriptTemplate.innerHTML.trim();
    }
    return '';
  })();

  // Entrada em modo edição
  board.addEventListener('click', function(e){
    const editBtn = e.target.closest('[data-inline-edit]');
    const titleEl = e.target.closest('.treino-title');
    let card = null;
    if(editBtn){
      card = editBtn.closest('.treino-card');
    } else if(titleEl) {
      card = titleEl.closest('.treino-card');
      if(card && card.dataset.inlineEditing !== '1'){
        enableTitleEditing(titleEl);
        return; // título inline sem abrir edição de exercícios automaticamente
      }
    } else if(e.target.closest('.placeholder-msg')) {
      card = e.target.closest('.treino-card');
    }
    if(!card) return;
    if(card.dataset.inlineEditing === '1') return;
    activateInline(card);
  });

  function activateInline(card){
    card.dataset.inlineEditing = '1';
    const placeholder = card.querySelector('.placeholder-msg');
    if(placeholder) placeholder.remove();

    const exerciseWrapper = card.querySelector('.exercise-wrapper');
    if(!exerciseWrapper) return;

    // Guardar estado antigo para possível cancelamento
    const snapshot = Array.from(exerciseWrapper.children).map(el => el.cloneNode(true));
    card._snapshotOriginal = snapshot;

    // Limpar readonly temporariamente
    exerciseWrapper.querySelectorAll('.exercise-form.readonly').forEach(r => r.remove());

    const form = document.createElement('form');
  form.className = 'inline-treino-form';
  form.innerHTML = '';

    const existing = card.querySelectorAll('[data-exercicio-id]');
    if(existing.length){
      existing.forEach(exDiv => {
        const block = createExerciseBlock(exerciciosSelectTemplate);
        // Preencher valores
        const select = block.querySelector('select[name="exercicio"]');
        const exercicioId = exDiv.getAttribute('data-exercicio-id');
        if(select) select.value = exercicioId;
        block.querySelector('input[name="carga"]').value = exDiv.getAttribute('data-carga') || '';
        block.querySelector('input[name="repeticoes"]').value = exDiv.getAttribute('data-repeticoes') || '';
        block.querySelector('input[name="descanso"]').value = exDiv.getAttribute('data-descanso') || '';
        form.appendChild(block);
      });
    } else {
      const firstBlock = createExerciseBlock(exerciciosSelectTemplate);
      form.appendChild(firstBlock);
    }

    // Área de ações local no rodapé do card
    let footerActions = card.querySelector('.card-inline-actions');
    if(!footerActions){
      footerActions = document.createElement('div');
      footerActions.className = 'card-inline-actions';
      footerActions.innerHTML = '<button type="button" data-action="salvar" class="btn-salvar-ex action-save" style="background:#2d7a2d;">Salvar</button><button type="button" data-action="cancelar" class="btn-salvar-ex action-cancel" style="background:#555;">Cancelar</button>';
      card.appendChild(footerActions);
    } else {
      footerActions.style.display = 'flex';
    }

    exerciseWrapper.appendChild(form);

    // Focar primeiro select
    const firstSelect = form.querySelector('select[name="exercicio"]');
    if(firstSelect) firstSelect.focus();
  }

  // Criação inline de novo treino
  if(createBtn){
    createBtn.addEventListener('click', function(){
      // Evitar multi-criação simultânea
      if(board.querySelector('.treino-card[data-novo="1"]')) return;
      const newCard = document.createElement('div');
      newCard.className = 'treino-card';
      newCard.dataset.novo = '1';
      newCard.innerHTML = `
         <h4 class="treino-title" data-edit-inline="1">Novo Treino</h4>
         <div class="exercise-wrapper"></div>
      `;
      board.prepend(newCard);
      activateInline(newCard);
      enableTitleEditing(newCard.querySelector('.treino-title'));
    });
  }

  function enableTitleEditing(titleEl){
    if(titleEl.dataset.editingTitle === '1') return;
    titleEl.dataset.editingTitle = '1';
    const original = titleEl.textContent.trim();
    const input = document.createElement('input');
    input.type = 'text';
    input.value = original;
    input.className = 'treino-title-input';
    input.style.width = '100%';
    input.style.textAlign = 'center';
    input.style.fontWeight = '700';
    titleEl.replaceWith(input);
    input.focus();
    input.select();

    function finalize(apply){
      const h4 = document.createElement('h4');
      h4.className = 'treino-title';
      h4.setAttribute('data-edit-inline','1');
      h4.textContent = apply ? (input.value.trim() || 'Treino') : original;
      input.replaceWith(h4);
    }

    input.addEventListener('keydown', ev => {
      if(ev.key === 'Enter'){ ev.preventDefault(); finalize(true); }
      else if(ev.key === 'Escape'){ ev.preventDefault(); finalize(false); }
    });
    input.addEventListener('blur', () => finalize(true));
  }

  // Delegação para botões internos (incluindo ações fora do form, como salvar/cancelar)
  board.addEventListener('click', function(e){
    const btn = e.target.closest('button[data-action]');
    if(!btn) return;
    const action = btn.dataset.action;
    const card = btn.closest('.treino-card');
    const form = card ? card.querySelector('.inline-treino-form') : null;

    if(action === 'add-more'){
      if(!form) return;
      const block = createExerciseBlock(exerciciosSelectTemplate);
      form.appendChild(block);
      return;
    }
    if(action === 'remove'){
      if(!form) return;
      const ex = btn.closest('.exercise-form.inline-edit');
      if(ex && form.querySelectorAll('.exercise-form.inline-edit').length > 1){
        ex.remove();
      }
      return;
    }
    if(action === 'cancelar'){
      if(card && form){
        form.remove();
      }
      if(card){
        if(card._snapshotOriginal){
          const wrapper = card.querySelector('.exercise-wrapper');
          wrapper.innerHTML = '';
          card._snapshotOriginal.forEach(node => wrapper.appendChild(node));
          delete card._snapshotOriginal;
        }
        delete card.dataset.inlineEditing;
        const footer = card.querySelector('.card-inline-actions');
        if(footer) footer.remove();
      }
      return;
    }
    if(action === 'salvar'){
      if(!card || !form){ return; }
      const isNovo = card.dataset.novo === '1' && !card.getAttribute('data-treino-id');
      const treinoId = card.getAttribute('data-treino-id');
      const fd = new FormData();
      // Ler nome (pode estar input ou h4)
      const titleInput = card.querySelector('.treino-title-input');
      const nomeTreino = titleInput ? titleInput.value.trim() : (card.querySelector('.treino-title')?.textContent?.trim());
      fd.append('nome', nomeTreino || 'Treino');
      form.querySelectorAll('.exercise-form.inline-edit').forEach(b => {
        fd.append('exercicio[]', b.querySelector('select[name="exercicio"]').value);
        fd.append('carga[]', b.querySelector('input[name="carga"]').value);
        fd.append('repeticoes[]', b.querySelector('input[name="repeticoes"]').value);
        fd.append('descanso[]', b.querySelector('input[name="descanso"]').value);
      });
      const csrfToken = getCsrfToken();
      btn.disabled = true; btn.textContent = 'Salvando...';
      const url = isNovo ? criarTreinoUrl : `/treinos/${treinoId}/editar/`;
      fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With':'XMLHttpRequest', 'X-CSRFToken': csrfToken },
        body: fd
      }).then(r => { if(!r.ok) throw new Error('Erro ao salvar'); return r.json(); })
        .then(data => {
          if(!data.ok) throw new Error('Resposta inválida');
          // Se novo, setar ID e injetar ações (concluir/excluir/editar)
          if(isNovo){
            card.setAttribute('data-treino-id', data.treino.id);
            delete card.dataset.novo;
            // Injetar barra de ações
            const actions = document.createElement('div');
            actions.className = 'treino-actions';
            actions.innerHTML = `
              <button type="button" class="edit-box" data-inline-edit title="Editar treino">✎</button>
              <form method="post" action="/treinos/${data.treino.id}/concluir/" class="inline-form">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <button type="submit" class="finish-box" title="Marcar como concluído">✓</button>
              </form>
              <form method="post" action="/treinos/${data.treino.id}/excluir/" class="inline-form" onsubmit="return confirm('Tem certeza que deseja excluir este treino?');">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <button type="submit" class="delete-box" title="Excluir treino">🗑</button>
              </form>`;
            card.appendChild(actions);
          }
          const wrapper = card.querySelector('.exercise-wrapper');
          if(form) form.remove();
          wrapper.innerHTML = '';
            data.treino.exercicios.forEach((ex, i) => {
              const tile = document.createElement('div');
              tile.className = 'exercise-form readonly';
              tile.setAttribute('data-exercicio-id', ex.exercicio_id);
              tile.setAttribute('data-carga', ex.carga || '');
              tile.setAttribute('data-repeticoes', ex.repeticoes || '');
              tile.setAttribute('data-descanso', ex.descanso || '');
              tile.innerHTML = `<div style=\"font-size:12px; font-weight:600;\">Exercício ${i+1}:</div>
                                <div>${ex.exercicio_nome}</div>
                                <div>Carga: ${ex.carga || ''} kg</div>
                                <div>Repetições: ${ex.repeticoes || ''}</div>
                                <div>Descanso: ${ex.descanso || ''} s</div>`;
              wrapper.appendChild(tile);
            });
          delete card.dataset.inlineEditing;
          delete card._snapshotOriginal;
          const footer = card.querySelector('.card-inline-actions');
          if(footer) footer.remove();
        }).catch(err => {
          console.error(err);
          btn.disabled = false; btn.textContent = 'Salvar';
          alert('Falha ao salvar exercícios.');
        });
    }
  });

  function getCsrfToken(){
    // Tenta obter do cookie; se base.html já injeta token em meta, pode adaptar
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    if(m) return m[1];
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // Removidas funções de barra global; ações agora ficam no card
})();
