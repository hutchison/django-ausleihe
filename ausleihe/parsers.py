from html.parser import HTMLParser


class LSFRoomParser(HTMLParser):
    room_name = ""
    in_table = False
    read_room_name = False

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_table = True

    def handle_data(self, data):
        data = data.strip()

        if not self.room_name and self.read_room_name and self.in_table:
            self.room_name = data
            self.read_room_name = False

        if data == "Raum":
            self.read_room_name = True

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_table = False
