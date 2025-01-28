const appHeight = () => {
    const doc = document.documentElement;
    doc.style.setProperty("--app-height", `${window.innerHeight}px`);
}
window.addEventListener("resize", appHeight);
appHeight();

const navHeight = () => {
    let offsetHeight = document.getElementById("navbar").offsetHeight;
    const doc = document.documentElement;
    doc.style.setProperty("--nav-height", `${offsetHeight}px`);
}
window.addEventListener("resize", navHeight);
navHeight();