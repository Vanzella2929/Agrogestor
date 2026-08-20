
// Manipulação da página de Animais

const animalForm = document.getElementById('animal-form');
if (animalForm) {
  animalForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const tag = document.getElementById('tag').value;
    const category = document.getElementById('category').value;
    const birthDate = document.getElementById('birth-date').value;
    const lot = document.getElementById('lot').value;

    const list = document.getElementById('animal-list');
    const row = document.createElement('tr');
    row.innerHTML = `<td>${tag}</td><td>${category}</td><td>${birthDate}</td><td>${lot}</td>`;
    list.appendChild(row);

    this.reset();
  });
}

// Manipulação da página de Financeiro
const financeForm = document.getElementById('finance-form');
if (financeForm) {
  financeForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const type = document.getElementById('type').value;
    const target = document.getElementById('target').value;
    const description = document.getElementById('description').value;
    const amount = parseFloat(document.getElementById('amount').value).toFixed(2);

    const list = document.getElementById('finance-list');
    const row = document.createElement('tr');
    row.innerHTML = `<td>${type}</td><td>${target}</td><td>${description}</td><td>R$ ${amount}</td>`;
    list.appendChild(row);

    this.reset();
  });
}