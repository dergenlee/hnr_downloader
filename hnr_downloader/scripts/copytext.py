
import os


def is_empty_line(str):
    return str.strip() == '' if str else None


def strip_endline(str):
    if str and str.endswith('\n'):
        return str[0:-1]
    else:
        return str


class Po(object):

    def __init__(self, file):
        self.file = file
        self.entries = {}

        self.read_entries()

    def read_entries(self):
        with open(self.file, 'r', encoding='utf-8') as f:
            line = f.readline()
            while line:
                comment, line = self.get_comment(f, line)
                if line:
                    msgid, line = self.get_msgid(f, line)
                if line:
                    msgstr, line = self.get_msgstr(f, line)
                if msgid:
                    self.entries.update({
                        msgid: {'comment': comment, 'msgstr': msgstr}
                    })

    def get_comment(self, f, line):
        while line and is_empty_line(line):
            line = f.readline()

        comment = ''
        while line and line.startswith('#'):
            comment += line
            line = f.readline()

        return strip_endline(comment), line

    def get_msgid(self, f, line):
        while line and is_empty_line(line):
            line = f.readline()

        msgid = None
        if line and line.startswith('msgid'):
            msgid = line.split(maxsplit=1)[1]
            line = f.readline()
            while line and line.startswith('"'):
                msgid += line
                line = f.readline()

        return strip_endline(msgid), line

    def get_msgstr(self, f, line):
        while line and is_empty_line(line):
            line = f.readline()

        msgstr = None
        if line and line.startswith('msgstr'):
            msgstr = line.split(maxsplit=1)[1]
            line = f.readline()
            while line and line.startswith('"'):
                msgstr += line
                line = f.readline()

        return strip_endline(msgstr), line

    def merge(self, pot):
        temp_entries = {}
        for key, value in pot.entries.items():
            v = self.entries.get(key, None)
            if v:
                temp_entries[key] = {
                    'comment': value.get('comment', ''),
                    'msgstr': v.get('msgstr', '')}
            else:
                temp_entries[key] = value
        self.entries = temp_entries

    def write_po(self):
        with open(self.file, 'w', encoding='utf-8') as f:
            for msgid, value in self.entries.items():
                f.write(f'{value.get("comment")}\n')
                f.write(f'msgid {msgid}\n')
                f.write(f'msgstr {value.get("msgstr")}\n\n')


def copyfile(source, dest):
    buffer_size = 1024 * 1024
    with open(source, 'rb') as src, open(dest, 'wb') as dst:
        while True:
            copy_buffer = src.read(buffer_size)
            if not copy_buffer:
                break
            dst.write(copy_buffer)


if __name__ == '__main__':
    locale = r'..\i18n\locale'
    pot = Po(r'..\i18n\locale\hnr.pot')
    for root, dirs, files in os.walk(locale):
        for file in files:
            if not file.endswith('.po'):
                continue
            pofile = os.path.join(root, file)
            copyfile(pofile, f'{pofile}.bak')

            po = Po(pofile)
            po.merge(pot)

            po.write_po()
