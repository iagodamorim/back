document.addEventListener("DOMContentLoaded", function () {
    window.quillInstance = Quill.find(document.querySelector('#editor'));
    console.log("Valor de window.quillInstance:", window.quillInstance);
});

    const chatInput = document.getElementById('chat-input');
    const chat = document.getElementById('chat');

    // Tecla enter envia resposta do usuário
    chatInput.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            if (event.shiftKey) {
                // Permite quebra de linha com Shift + Enter
                const cursorPosition = chatInput.selectionStart;
                chatInput.value = chatInput.value.substring(0, cursorPosition) + '\n' + chatInput.value.substring(cursorPosition);
                event.preventDefault(); // Evita o comportamento padrão do Enter
            } else {
                // Envia a mensagem com Enter
                let userMessage = chatInput.value.trim();
                if (userMessage) {
                    // Substitui quebras de linha por //
                    userMessage = userMessage.replace(/\n/g, ' // ');

                    // Adiciona mensagem do usuário
                    const messageElement = document.createElement('pre');
                    messageElement.textContent = `Usuário: ${userMessage}`;
                    messageElement.style.margin = "5px 0";
                    chat.appendChild(messageElement);

                    // Limpa o campo de entrada
                    chatInput.value = '';

                    // Enviar dados para o backend
                    sendDataToBackend(userMessage);
                }
                event.preventDefault(); // Evita o comportamento padrão do Enter
            }
        }
    });

    // Função para enviar mensagem ao backend e exibir a resposta
    function sendDataToBackend(userMessage) {
        const chatMessages = [...chat.children].map(child => child.textContent);
        const textFieldContent = window.quillInstance.root.innerHTML;

        const payload = {
            chat: chatMessages,
            textField: textFieldContent
        };

        fetch('/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                if (data.response) {
                    // Exibe a resposta do backend no chat
                    const systemMessage = document.createElement('div');
                    systemMessage.textContent = `Sistema: ${data.response}`;
                    systemMessage.style.margin = "5px 0";
                    systemMessage.style.color = "blue";
                    chat.appendChild(systemMessage);
                    chat.scrollTop = chat.scrollHeight; // Rolagem automática

                    // Atualiza o campo de texto
                    if (data.updatedTextField) {
                        const formattedText = data.updatedTextField.replace(/\n/g, '<br>');
                        window.quillInstance.clipboard.dangerouslyPasteHTML(formattedText);
                    }
                } else {
                    console.error("Erro na resposta:", data.error);
                }
            })
            .catch(error => {
                console.error("Erro ao enviar dados ao backend:", error);
            });
    }



