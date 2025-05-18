const quotes = [
    "“An investment in knowledge pays the best interest.” – Benjamin Franklin",
    "“Do not save what is left after spending, but spend what is left after saving.” – Warren Buffett",
    "“The stock market is filled with individuals who know the price of everything, but the value of nothing.” – Philip Fisher",
    "“It’s not your salary that makes you rich, it’s your spending habits.” – Charles A. Jaffe",
    "“Beware of little expenses. A small leak will sink a great ship.” – Benjamin Franklin"
];

let currentQuote = 0;
const quoteBox = document.getElementById("quoteBox");

function showNextQuote() {
    quoteBox.style.opacity = 0;
    setTimeout(() => {
        currentQuote = (currentQuote + 1) % quotes.length;
        quoteBox.textContent = quotes[currentQuote];
        quoteBox.style.opacity = 1;
    }, 800);
}

setInterval(showNextQuote, 5000);
window.onload = () => {
    quoteBox.style.opacity = 1;
};
