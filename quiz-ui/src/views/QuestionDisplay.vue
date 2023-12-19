<script setup>
import { ref, onMounted } from 'vue';

const emit = defineEmits(['click-on-answer']);
const props = defineProps({
  currentQuestion: Object
});
onMounted(async () => {
		console.log("Question display page mounted");
    console.log(props.currentQuestion);
});


</script>

<template>
  <h1>Question Display page</h1>

  <!--
  <h2> {{  currentQuestion.title }}</h2>
  
  <h4> {{ currentQuestion.text }}</h4>
  -->
  <!--
  <img v-if="props.currentQuestion.image" :src="props.currentQuestion.image" />
  <a v-for="(answer, index) in props.currentQuestion.possibleAnswers" 
   @click="emit('click-on-answer', index)">{{ answer.text }}</a>
  -->

</template>