(function(){

  if(!window.__GRAFICO__){return;}
  const { mensalLabels, mensalValues, anualLabels, anualValues } = window.__GRAFICO__;

  const ctx = document.getElementById('graficoTreinos');
  if(!ctx) return;

  function buildDataset(labels, values, titulo){
    return {
      type: 'bar',
      data: { labels, datasets: [{
        label: titulo,
        data: values,
        backgroundColor: '#4b6cb7'
      }]},
      options: {
        responsive: true,
        animation: false,
        scales: { y: { beginAtZero: true, ticks: { precision:0 } } }
      }
    };
  }

  let chartInstance = new Chart(ctx, buildDataset(mensalLabels, mensalValues, 'Dias treinados (últimas 4 semanas)'));

  function switchChart(mode){
    chartInstance.destroy();
    if(mode==='anual'){
      chartInstance = new Chart(ctx, buildDataset(anualLabels, anualValues, 'Dias treinados por mês'));
    } else {
      chartInstance = new Chart(ctx, buildDataset(mensalLabels, mensalValues, 'Dias treinados (últimas 4 semanas)'));
    }
  }

  document.querySelectorAll('.tab-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('ativo'));
      btn.classList.add('ativo');
      switchChart(btn.dataset.chart);
    });
  });

  const defaultBtn = document.querySelector('.tab-btn[data-chart="mensal"]');
  if(defaultBtn) defaultBtn.classList.add('ativo');
})();
