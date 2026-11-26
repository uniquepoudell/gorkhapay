// Estimate calculator: shows roughly how many NPR each provider delivers. Estimates only.
(function () {
  var form = document.getElementById("calc");
  var input = document.getElementById("amount");
  var list = document.getElementById("provs");
  if (!form || !input || !list) return;
  var rate = parseFloat(form.getAttribute("data-rate")) || 0;
  var fmt = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
  function update() {
    var amount = parseFloat(input.value) || 0;
    var cards = Array.prototype.slice.call(list.querySelectorAll(".prov"));
    cards.forEach(function (c) {
      var fee = parseFloat(c.getAttribute("data-fee")) || 0;
      fee += amount * (parseFloat(c.getAttribute("data-fee-pct")) || 0) / 100;
      var margin = parseFloat(c.getAttribute("data-margin")) || 0;
      var npr = Math.max(amount - fee, 0) * rate * (1 - margin / 100);
      c._npr = npr;
      c.classList.remove("best");
      var b = c.querySelector(".badge"); if (b) b.remove();
      c.querySelector(".receive").innerHTML = "≈ NPR " + fmt.format(npr) + "<small>estimate</small>";
    });
    cards.sort(function (a, b) { return b._npr - a._npr; }).forEach(function (c) { list.appendChild(c); });
    if (cards.length && amount > 0) {
      cards[0].classList.add("best");
      var s = document.createElement("span"); s.className = "badge"; s.textContent = "Best estimate";
      cards[0].querySelector("h3").appendChild(s);
    }
  }
  input.addEventListener("input", update);
  update();
})();
