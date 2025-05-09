from utils import add_task, delay

class Process:
    def __init__(self, functions):
        self.functions = functions

    def process_command(self, response):
        clean_response = []
        i = 0
        length = len(response)

        while i < length:
            if response[i:i+4] == "prs(":
                j = response.find(")", i)
                if j != -1:
                    add_task(self.functions.press, response[i+4:j])
                    i = j

            elif response[i:i+4] == "dom(":
                j = response.find(")", i)
                if j != -1:
                    add_task(self.functions.play_macro, response[i+4:j])
                    i = j

            elif response[i:i+4] == "clp;":
                add_task(self.functions.save_clip)
                i += 3

            elif response[i:i+4] == "dly(":
                j = response.find(")", i)
                if j != -1:
                    delay_time = float(response[i+4:j])
                    add_task(delay, delay_time) 
                    i = j

            elif response[i:i+4] == "msg(":
                j = response.find(")", i)
                if j != -1:
                    content = response[i+4:j].strip()
                    if content.endswith("true"):
                        add_task(self.functions.chat, content[:-4].strip(), True)
                    elif content.endswith("false"):
                        add_task(self.functions.chat, content[:-5].strip(), False)
                    i = j

            elif response[i:i+4] == "hld(":
                j = response.find(")", i)
                if j != -1:
                    content = response[i+4:j].strip()
                    parts = content.split(maxsplit=1)
                    if len(parts) == 2:
                        button, duration = parts
                        try:
                            duration = float(duration)
                            add_task(self.functions.hold, button, duration)
                        except ValueError:
                            print(f"Invalid duration in hld: {content}")
                    i = j

            elif response[i:i+4] == "mut;":
                self.functions.toggle_mute()
                i += 3

            elif response[i:i+4] == "ret;":
                add_task(self.functions.retreat) 
                i += 3

            elif response[i:i+4] == "ply(":
                j = response.find(")", i)
                if j != -1:
                    add_task(self.functions.play_sound_effect, response[i+4:j])
                    i = j

            elif response[i:i+4] == "non;":
                add_task(self.functions.nod_no)
                i += 3

            elif response[i:i+4] == "noy;":
                add_task(self.functions.nod_yes)
                i += 3

            else:
                clean_response.append(response[i])

            i += 1

        return "".join(clean_response).strip()

