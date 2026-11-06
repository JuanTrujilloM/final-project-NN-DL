const samplePosts = [
  { author: "Red Comunitaria Cali", handle: "@redcomunitaria", time: "hace 12 min", text: "Se necesita agua y comida para las familias del barrio El Poblado. ¿Alguien puede apoyar con suministros?", label: "requests_or_urgent_needs", labelName: "Solicitudes o necesidades urgentes", confidence: 0.88 },
  { author: "Noticias del Eje", handle: "@noticiaseje", time: "hace 26 min", text: "La vía principal permanece bloqueada por un derrumbe tras las fuertes lluvias. Tránsito recomienda tomar rutas alternas.", label: "infrastructure_and_utility_damage", labelName: "Daños en infraestructura", confidence: 0.81 },
  { author: "Defensa Civil local", handle: "@defensacivil", time: "hace 41 min", text: "Voluntarios se reúnen en la plaza para organizar brigadas de rescate y recibir donaciones.", label: "rescue_volunteering_or_donation_effort", labelName: "Rescate, voluntariado o donaciones", confidence: 0.76 },
  { author: "María Fernanda", handle: "@mfernanda_co", time: "hace 1 h", text: "Mucha fuerza a todas las personas afectadas. No están solas, la comunidad está acompañando.", label: "sympathy_and_support", labelName: "Simpatía y apoyo", confidence: 0.69 },
];

const state = { posts: [...samplePosts] };
const feed = document.querySelector("#feed-list");
const filter = document.querySelector("#category-filter");
const modelSelect = document.querySelector("#model-select");
const textInput = document.querySelector("#tweet-text");
const errorMessage = document.querySelector("#composer-error");

function confidenceClass(value) {
  return value >= 0.7 ? "high" : value >= 0.4 ? "medium" : "low";
}

function renderPosts() {
  const selected = filter.value;
  const posts = state.posts.filter((post) => {
    const matchesCategory = selected === "all" || post.label === selected;
    return matchesCategory;
  });
  document.querySelector("#post-count").textContent = `${posts.length} publicaciones`;
  feed.innerHTML = posts.map((post) => `
    <article class="post card">
      <div class="post-header">
        <div class="avatar avatar-green">CO</div>
        <div><div class="post-author">${post.author} <span class="post-handle">${post.handle} · ${post.time}</span></div></div>
      </div>
      <p class="post-text">${escapeHtml(post.text)}</p>
      <div class="prediction">
        <span class="tag">${post.labelName}</span>
        <span class="confidence-label"><span class="confidence ${confidenceClass(post.confidence)}"></span> Confianza <strong>${Math.round(post.confidence * 100)}%</strong></span>
      </div>
    </article>
  `).join("") || '<div class="card post">No hay publicaciones en esta categoría.</div>';
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[character]);
}

async function analyzePost() {
  const text = textInput.value.trim();
  if (!text) {
    errorMessage.textContent = "Escribe una publicación para analizarla.";
    return;
  }
  const button = document.querySelector("#analyze-button");
  button.disabled = true;
  errorMessage.textContent = "";
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, model: modelSelect.value }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "No fue posible analizar la publicación.");
    state.posts.unshift({
      author: "Nueva publicación",
      handle: "@analisis_local",
      time: "ahora",
      text,
      label: result.label,
      labelName: result.label_name,
      confidence: result.confidence,
    });
    textInput.value = "";
    updateCount();
    renderPosts();
  } catch (error) {
    errorMessage.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function updateCount() {
  document.querySelector("#char-count").textContent = `${textInput.value.length}/280`;
}

fetch("/models")
  .then((response) => response.json())
  .then((models) => {
    models.forEach((model) => {
      const option = document.createElement("option");
      option.value = model.id;
      option.textContent = `${model.name}${model.status === "demo" ? " · demo" : ""}`;
      modelSelect.append(option);
    });
  })
  .catch((error) => { errorMessage.textContent = error.message; });

const categories = [
  ["caution_and_advice", "Precauciones y consejos"],
  ["displaced_people_and_evacuations", "Desplazados y evacuaciones"],
  ["infrastructure_and_utility_damage", "Daños en infraestructura"],
  ["injured_or_dead_people", "Heridos o muertos"],
  ["missing_or_found_people", "Personas desaparecidas"],
  ["not_humanitarian", "No humanitario"],
  ["other_relevant_information", "Otra información relevante"],
  ["requests_or_urgent_needs", "Solicitudes o necesidades urgentes"],
  ["rescue_volunteering_or_donation_effort", "Rescate, voluntariado o donaciones"],
  ["sympathy_and_support", "Simpatía y apoyo"],
];
categories.forEach(([value, name]) => filter.add(new Option(name, value)));
textInput.addEventListener("input", updateCount);
filter.addEventListener("change", renderPosts);
document.querySelector("#analyze-button").addEventListener("click", analyzePost);
document.querySelectorAll("[data-scroll-to]").forEach((element) => {
  element.addEventListener("click", () => {
    document.getElementById(element.dataset.scrollTo).scrollIntoView({ behavior: "smooth" });
    textInput.focus();
  });
});
renderPosts();
