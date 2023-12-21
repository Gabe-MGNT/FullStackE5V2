

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
     def __init__(self,text:str, is_correct:bool):
          self.text = text
          self.is_correct = is_correct

     def to_dict(self):
        return {
            'text': self.text,
            'isCorrect': self.is_correct
        }

     @classmethod
     def from_dict(cls, data):
        return cls(data['text'], data['isCorrect'])
     
class ParticipationResult:
     def __init__(self, playerName, score, answersSummaries):
            self.playerName = playerName
            self.score = score
            self.answersSummaries = answersSummaries

"""
Pour les participations : idée

Utiliser un token de session qu'on va stocker dans un table qui aura :
le token de session, le pseudo du joueur, la question actuelle et les réponses fournies sous forme de liste
"""