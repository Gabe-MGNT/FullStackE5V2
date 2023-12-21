<script setup>
import { ref, onMounted } from 'vue';
import QuestionDisplay from "@/views/QuestionDisplay.vue";
import quizApiService from "@/services/QuizApiService";

import { useRouter } from 'vue-router';

const router = useRouter();

var currentQuestion = ref({});
var currentQuestionPosition = ref(1);
var totalNumberOfQuestion = ref(1);

var answersArray = [];

const loadQuestionByPosition = async () => {

    
    let responseQuestion = await quizApiService.getQuestion(currentQuestionPosition.value);
    currentQuestion.value = responseQuestion.data;

};  

const answerClickedHandler = async (index) => {
    // Lorsque réponse cliquée

    //Récupérer les infos de la réponse cliquée et envoyer en BDD
    answersArray.push(index);

    console.log(answersArray)


    // Dire que la question actuelle s'incrémente (passe à la suivante)
    currentQuestionPosition.value++;

    if (currentQuestionPosition.value > totalNumberOfQuestion.value) {
        endQuiz();
        return;
    }

    // Récupérer la nouvelle question (actualiser currentQuestion)
    await loadQuestionByPosition();

}; 
const endQuiz = async () => {
    // Lorsque le quiz est terminé

    // Calculer score avec /participations


    // Stocker score en local

    // Rediriger vers la page de fin de quiz
    router.push('/scores');
};   




onMounted(async () => {
		console.log("Question manager page mounted");
        // (nb total) Le laisser dans mounted ou le mettre dans local storage (solution moins bien je trouve)
        // Ca dépend si onMounted est appelé à chaque fois
        let response = await quizApiService.getQuizInfo();
        totalNumberOfQuestion.value = response.data.size;

        await loadQuestionByPosition();
});


</script>

<template>
  <h1>Question Manager page</h1>

   
  <h1>Question {{ currentQuestionPosition }} / {{ totalNumberOfQuestion }}</h1>
  
    <!-- Render QuestionDisplay only when currentQuestion is not undefined -->
    <QuestionDisplay v-if="currentQuestion" :currentQuestion="currentQuestion" @click-on-answer="answerClickedHandler" />

    <!-- Show loading message when currentQuestion is undefined -->
    <div v-else>Loading...</div>

</template>