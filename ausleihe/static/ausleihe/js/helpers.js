function hide(element) {
	element.classList.add("d-none");
}

function show(element) {
	element.classList.remove("d-none");
}

/* Suchfunktion
 * Sucht in selector nach query und zeigt nur die Elemente an, die query enthalten.
 */
function display_filter(selector, query) {
	query = query.trim().toLowerCase();
	document.querySelectorAll(selector).forEach(elem => {
		if (elem.innerText.toLowerCase().search(query) < 0) { // nichts gefunden
			hide(elem);
		} else {
			show(elem);
		}
	});
}
