function enter_next(event) {
	if (event.which == 13) {
		event.preventDefault();
	}
	var $this = $(event.target);
	var index = parseInt($this.attr("data-index"));
	$('[data-index="' + (index + 1).toString() + '"]').focus();
}
