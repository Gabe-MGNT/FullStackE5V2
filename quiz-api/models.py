

class Question:
    def __init__(self, position:int, title:str, text:str, image:str, possibleAnswers:list=[], id:int=None):
        self.position = position
        self.title = title
        self.text = text
        self.image = image
        self.possibleAnswers = []
        self.id = id

    def to_dict(self):
            return {
                'position': self.position,
                'title': self.title,
                'text': self.text,
                'image': self.image,
                'possibleAnswers': self.possibleAnswers,
                "id":self.id,
            }

    @classmethod
    def from_dict(cls, data):
        return cls(data['position'], data['title'], data['text'], data['image'], data['possibleAnswers'])
    


class Answer:
     def __init__(self,text:str, isCorrect:bool):
          self.text = text
          self.isCorrect = isCorrect

     def to_dict(self):
        return {
            'text': self.text,
            'isCorrect': self.isCorrect
        }

     @classmethod
     def from_dict(cls, data):
        return cls(data['text'], data['isCorrect'])