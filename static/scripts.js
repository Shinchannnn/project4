let data = null;
let selectedKey = null;
// Fetch data from backend
fetch('/api/data')
.then(response => response.json())
.then(jsonData => {
data = jsonData;
console.log('Data:', data);
})
.catch(error => console.error('Error:', error));
function mainSearch(input) {
console.log('mainSearch:', input);
if (!data) return; // Check if data is loaded
const keys = [];
const values = [];
function traverse(obj) {
for (const key in obj) {
if (key.toLowerCase().includes(input.toLowerCase())) keys.push(key);
const value = obj[key];
if (typeof value === "string" && value.toLowerCase().includes(input.toLowerCase())) {
values.push(value);
} else if (typeof value === "object") {
traverse(value);
}
}
}
traverse(data);
document.getElementById('key_results').innerHTML = keys.length
? keys.map(k => <p onclick="selectKey('${k}')">${k}</p>).join('')
: 'No matching keys found.';
}
function searchKeys(input) {
if (!data) return; // Check if data is loaded
const keys = Object.keys(data).filter(key => key.toLowerCase().includes(input.toLowerCase()));
document.getElementById('key_results').innerHTML = keys.length
? keys.map(k => <p onclick="selectKey('${k}')">${k}</p>).join('')
: 'No matching keys found.';
}
function searchValues(input) {
if (!data) return; // Check if data is loaded
if (!selectedKey) {
document.getElementById('value_results').innerHTML = 'Select a valid key first.';
return;
}
const values = [];
function traverse(obj) {
for (const key in obj) {
if (key === selectedKey) {
const value = obj[key];
if (typeof value === "string" && value.toLowerCase().includes(input.toLowerCase())) {
values.push(value);
} else if (typeof value === "object") {
traverse(value);
}
}
}
}
traverse(data);
document.getElementById('value_results').innerHTML = values.length
? values.map(v => <p onclick="selectValue('${v}')">${v}</p>).join('')
: 'No matching values found.';
}
function selectKey(key) {
selectedKey = key;
document.getElementById('key_search').value = key;
document.getElementById('value_results').innerHTML = ''; // Clear value results
searchValues(''); // Trigger searchValues with empty input
}
function selectValue(value) {
document.getElementById('value_search').value = value;
document.getElementById('selected_results').innerHTML =
Selected Key: ${selectedKey}<br>Selected Value: ${value};
}
document.getElementById('value_search').addEventListener('input', function() {
searchValues(this.value);
});