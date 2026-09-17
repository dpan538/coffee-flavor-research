import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";
import { startUpdates } from "./update";

document.documentElement.dataset.build = __BUILD_ID__;
createApp(App).mount("#app");
startUpdates();
