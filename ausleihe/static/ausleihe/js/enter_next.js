function enter_next(event) {
	if (event.which == 13) {
		event.preventDefault();
		let index = parseInt($(event.target).attr("data-index"));
		var next_element = $('[data-index="' + (index + 1).toString() + '"]');

		if (next_element.length == 1) {
			var e = next_element[0];
			if (e.classList.contains("selectized")) {
				e.selectize.focus();
			} else {
				e.focus();
			}
		}
	}
}
