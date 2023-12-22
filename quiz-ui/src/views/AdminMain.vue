<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import quizApiService from "@/services/QuizApiService";
import participationStorageService from "@/services/ParticipationStorageService";
import { all } from 'axios';

const token = ref('');

var allQuestion = ref([]);

onMounted(async () => {
		console.log("Admin main page mounted");
        token.value = participationStorageService.getToken();
        let response = await quizApiService.getAllQuestions(token.value);

        allQuestion.value = response.data.questions;

        console.log(allQuestion.value);

});
</script>
<template>
    <div>
      <div v-for="(question, index) in allQuestion" :key="index">
        <h2>{{ question.title }}</h2>
        <p>{{ question.text }}</p>
      </div>
    </div>
  </template>
  
  
  