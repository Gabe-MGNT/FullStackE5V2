<script setup>
import { ref, onMounted } from 'vue';
import participationStorageService from "@/services/ParticipationStorageService";

import { useRouter } from 'vue-router';

var username = ref('');
const router = useRouter();

function launchNewQuiz() {
  console.log("Launch new quiz with", username.value);
  participationStorageService.savePlayerName(username.value);
  router.push('/questions');
}

onMounted(async () => {
		console.log("Quizz page mounted");
});


</script>

<template>
  <h1>New Quiz page</h1>


  <p>Saisissez votre nom :</p>
  <input type="text" id="playerName" name="playerName" v-model="username"><br><br>
  <p>{{  username }}</p>  
  <button @click="launchNewQuiz">GO!</button>  


</template>