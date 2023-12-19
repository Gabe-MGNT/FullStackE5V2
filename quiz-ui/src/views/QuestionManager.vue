<script setup>
import { ref, onMounted } from 'vue';
import QuestionDisplay from "@/views/QuestionDisplay.vue";
import quizApiService from "@/services/QuizApiService";

var currentQuestion = ref({});
var currentQuestionPosition = ref(1);
var totalNumberOfQuestion = ref(1);

const loadQuestionByPosition = async () => {

    
    let responseQuestion = await quizApiService.getQuestion(currentQuestionPosition.value);
    currentQuestion.value = responseQuestion.data;

};  

const answerClickedHandler = (index) => {
    // Lorsque réponse cliquée

    //Récupérer les infos de la réponse cliquée et envoyer en BDD


    // Dire que la question actuelle s'incrémente (passe à la suivante)
    currentQuestionPosition.value++;

    // Récupérer la nouvelle question (actualiser currentQuestion)
    loadQuestionByPosition();

}; 
const endQuiz = () => {
    // Lorsque le quiz est terminé

    // Calculer score en BDD

    // Rediriger vers la page de fin de quiz
};   




onMounted(async () => {
		console.log("Question manager page mounted");
        // (nb total) Le laisser dans mounted ou le mettre dans local storage (solution moins bien je trouve)
        // Ca dépend si onMounted est appelé à chaque fois
        let response = await quizApiService.getQuizInfo();
        totalNumberOfQuestion.value = response.data.size;

        currentQuestion.value = await loadQuestionByPosition();
});


</script>

<template>
  <h1>Question Manager page</h1>

   
  <h1>Question {{ currentQuestionPosition }} / {{ totalNumberOfQuestion }}</h1>
  
  <QuestionDisplay :currentQuestion="currentQuestion" @click-on-answer="answerClickedHandler" />


</template>