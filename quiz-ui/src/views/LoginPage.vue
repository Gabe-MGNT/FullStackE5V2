<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import quizApiService from "@/services/QuizApiService";
import participationStorageService from "@/services/ParticipationStorageService";

const router = useRouter();
var password = ref('');
var loginError = ref('');
var token = ref('');  // Declare token here

const loginAdmin = async () => {
  console.log("Log in with", password.value);
  try {
    const response = await quizApiService.login(password.value);
    if (response.status === 200) {
      loginError.value = '';
      token = response.data.token;
      participationStorageService.saveToken(token);

      console.log("Login successful");
      router.push('/admin-main');
    } else {
      console.log("Login incorrect");
      loginError.value = 'Incorrect password';
    }
  } catch (error) {
    console.log(error);
    if (error.response && error.response.status === 401) {
      loginError.value = 'Incorrect password';
    } else {
      loginError.value = 'Login failed';
    }
  }
};

onMounted(async () => {
		console.log("Login page mounted");
});


</script>

<template>
  <h1>Login page</h1>

  <p>Saisissez votre mot de passe administrateur :</p>
  <input type="text" id="playerName" name="playerName" v-model="password"><br><br>
  <p>{{ password }}</p>
  <button @click="loginAdmin">Log-in</button>  
  <p>{{ loginError }}</p>



</template>