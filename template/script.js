document.getElementById('platform-form').addEventListener('submit', async (event) => {
    event.preventDefault();
  
    const loadingIndicator = document.getElementById('loading');
    const responseOutput = document.getElementById('response-output');
    loadingIndicator.style.display = 'block'; // Mostrar o indicador de carregamento
    responseOutput.textContent = ''; // Limpar a saída anterior
  
    // Obter os valores dos inputs
    const formData = new FormData(event.target);
    const data = {
      instagram: formData.get('instagram') ? [formData.get('instagram')] : [],
      linkedin: formData.get('linkedin') ? [formData.get('linkedin')] : [],
      youtube: formData.get('youtube') ? [formData.get('youtube')] : [],
      tiktok: formData.get('tiktok') ? [formData.get('tiktok')] : []
    };
  
    try {
        const response = await fetch('http://127.0.0.1:8000/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
            });
  
      if (response.ok) {
        const result = await response.json();
        responseOutput.textContent = JSON.stringify(result, null, 2);
      } else {
        responseOutput.textContent = `Erro: ${response.status} ${response.statusText}`;
      }
    } catch (error) {
      responseOutput.textContent = `Erro ao conectar ao backend: ${error.message}`;
    } finally {
      loadingIndicator.style.display = 'none'; // Esconder o indicador de carregamento
    }
  });
  