

class Question:
    def __init__(self, position:int, title:str, text:str, image:str):
        self.position = position
        self.title = title
        self.text = text
        self.image = image

    def to_dict(self):
            return {
                'position': self.position,
                'title': self.title,
                'text': self.text,
                'image': self.image
            }

    @classmethod
    def from_dict(cls, data):
        return cls(data['position'], data['title'], data['text'], data['image'])