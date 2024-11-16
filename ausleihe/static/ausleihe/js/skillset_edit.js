var chosen_skillsetitems = new Set();

function add_skillsetitem() {
	let skillsetitems = document.getElementsByClassName("skillsetitem");
	let n = skillsetitems.length;
	let last = skillsetitems[n-1];
	let c = last.cloneNode(true);

	c.querySelector("[name='item_quantities']").value = '';
	c.querySelector("[name='item_ids']").value = '';
	c.addEventListener("change", check_skillsetitems);

	last.after(c);
}

function check_skillsetitems() {
	chosen_skillsetitems.clear();
	let submit_button = document.getElementById("submit-id-submit");
	submit_button.disabled = false;

	for (elem of document.getElementsByTagName("select")) {
		elem.classList.remove("is-invalid");

		if (elem.value) {
			if (chosen_skillsetitems.has(elem.value)) {
				elem.classList.add("is-invalid");
				submit_button.disabled = true;
			} else {
				chosen_skillsetitems.add(elem.value);
			}
		}
	}
}

document.addEventListener("DOMContentLoaded",
	() => {
		document.getElementById("add_item").addEventListener("click", add_skillsetitem);
		for (elem of document.getElementsByTagName("select")) {
			elem.addEventListener("change", check_skillsetitems);
		}
		check_skillsetitems();
	}
);
