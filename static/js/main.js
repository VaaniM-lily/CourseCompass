document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("onboardingForm");

  if (form) {
    const steps = [...form.querySelectorAll(".quiz-step")];
    const nextButton = document.getElementById("nextStep");
    const prevButton = document.getElementById("prevStep");
    const submitButton = document.getElementById("submitQuiz");
    let current = 0;

    function showStep(index) {
      steps.forEach((step, i) => step.classList.toggle("active", i === index));
      prevButton.disabled = index === 0;

      if (index === steps.length - 1) {
        nextButton.classList.add("hidden");
        submitButton.classList.remove("hidden");
      } else {
        nextButton.classList.remove("hidden");
        submitButton.classList.add("hidden");
      }
    }

    nextButton.addEventListener("click", () => {
      if (current < steps.length - 1) { current += 1; showStep(current); }
    });

    prevButton.addEventListener("click", () => {
      if (current > 0) { current -= 1; showStep(current); }
    });

    showStep(current);
  }

  setTimeout(() => {
    document.querySelectorAll(".flash").forEach((message) => {
      message.style.opacity = "0";
      message.style.transition = "opacity .4s ease";
      setTimeout(() => message.remove(), 400);
    });
  }, 4500);
});
