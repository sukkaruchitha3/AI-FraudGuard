// Auto welcome message when page loads

window.onload = function () {

let chatWindow = document.getElementById("chat-window");

chatWindow.innerHTML += `
<div class="bot-msg">
Hello 👋 I am your Financial Safety Assistant.<br>
Ask me about scams, OTP fraud, loan traps, BNPL risks, investment safety, or cybercrime reporting.
</div>
`;

};



// Send message function

function sendMessage() {

    const inputField = document.getElementById("chat-input");
    const userInput = inputField.value.trim();

    if (!userInput) return;

    appendMessage("You: " + userInput);

    fetch("/chatbot", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "message=" + encodeURIComponent(userInput)
    })
    .then(res => res.json())
    .then(data => {
        appendMessage("Bot: " + data.response);
    });

    inputField.value = "";
}



// ENTER KEY SUPPORT (like ChatGPT)

document.addEventListener("DOMContentLoaded", function(){

let input = document.getElementById("chat-input");

input.addEventListener("keypress", function(event){

if(event.key === "Enter"){

event.preventDefault();

sendMessage();

}

});

});