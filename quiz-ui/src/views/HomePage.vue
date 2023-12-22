<script setup>
import { ref, onMounted } from 'vue';
import quizApiService from "@/services/QuizApiService";

const registeredScores = ref([]);

onMounted(async () => {
		console.log("Home page mounted");
    registeredScores.value = quizApiService.getQuizInfo();
});


</script>

<template>
  <h1>Home page</h1>

  <div v-for="scoreEntry in registeredScores" v-bind:key="scoreEntry.date">
  {{ scoreEntry.playerName }} - {{ scoreEntry.score }}
  </div>

  <router-link to="/new-quiz">Démarrer le quiz !</router-link>
  <router-link to="/login">Login Admin</router-link>
</template>