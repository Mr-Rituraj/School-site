// ---------------------------------------------------------------------
// Live "bell schedule" indicator — reads the schedule embedded by Flask
// ---------------------------------------------------------------------
(function () {
  const widget = document.getElementById("bell-text");
  if (!widget) return;

  // Mirrors BELL_SCHEDULE in app.py so the ticker works from any page.
  const schedule = [
    [9, 0, "Prayer"],
	[9, 30, "Period 1"],
    [10, 15, "Period 2"],
    [10, 50, "Period 3"],
    [11, 25, "Period 4"],
    [12, 00, "Period 5"],
    [12, 30, "Lunch break"],
    [13, 00, "Period 6"],
    [13, 30, "Period 7"],
    [14, 0, "Day ends"],
  ];

  function updateBell() {
    if (!schedule.length) {
      widget.textContent = "School office: 9:00–14:00";
      return;
    }
    const now = new Date();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();

    let current = null;
    let next = null;

    for (let i = 0; i < schedule.length; i++) {
      const [h, m, label] = schedule[i];
      const mins = h * 60 + m;
      if (mins <= nowMinutes) {
        current = label;
      } else {
        next = { label, mins };
        break;
      }
    }

    if (!current) {
      widget.textContent = "Before school hours · office opens 9:00";
    } else if (!next) {
      widget.textContent = `${current} · school day complete`;
    } else {
      const until = next.mins - nowMinutes;
      widget.textContent = `${current} · ${next.label} in ${until} min`;
    }
  }

  updateBell();
  setInterval(updateBell, 30000);
})();

// ---------------------------------------------------------------------
// Scroll reveal for elements marked .reveal
// ---------------------------------------------------------------------
(function () {
  const items = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || items.length === 0) {
    items.forEach((el) => el.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  items.forEach((el) => observer.observe(el));
})();

// ---------------------------------------------------------------------
// Carousels (achievements + gallery slideshows) — forward-only, no
// backward navigation by design: no prev arrow, dots are indicators
// only (not clickable), and any swipe simply advances to the next slide.
// ---------------------------------------------------------------------
(function () {
  const carousels = document.querySelectorAll(".carousel");

  carousels.forEach((carousel) => {
    const track = carousel.querySelector(".carousel-track");
    const slides = Array.from(carousel.querySelectorAll(".carousel-slide"));
    const dotsWrap = carousel.querySelector(".carousel-dots");
    const nextBtn = carousel.querySelector(".next");
    if (!track || slides.length === 0) return;

    let index = 0;
    const autoplayDelay = parseInt(carousel.dataset.autoplay, 10) || 0;
    let timer = null;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    slides.forEach((_, i) => {
      const dot = document.createElement("span");
      dot.setAttribute("aria-hidden", "true");
      if (i === 0) dot.classList.add("is-active");
      dotsWrap.appendChild(dot);
    });
    const dots = Array.from(dotsWrap.children);

    function render() {
      track.style.transform = `translateX(-${index * 100}%)`;
      dots.forEach((d, i) => d.classList.toggle("is-active", i === index));
    }

    function next() {
      index = (index + 1) % slides.length;
      render();
      restart();
    }

    function restart() {
      if (timer) clearInterval(timer);
      if (autoplayDelay && !reduceMotion) {
        timer = setInterval(next, autoplayDelay);
      }
    }

    if (nextBtn) nextBtn.addEventListener("click", next);
    carousel.addEventListener("mouseenter", () => timer && clearInterval(timer));
    carousel.addEventListener("mouseleave", restart);

    // Swipe support: any swipe (either direction) just advances forward,
    // consistent with the no-backward-movement design.
    let startX = null;
    track.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
    track.addEventListener("touchend", (e) => {
      if (startX === null) return;
      const diff = e.changedTouches[0].clientX - startX;
      if (Math.abs(diff) > 40) next();
      startX = null;
    });

    render();
    restart();
  });
})();

// ---------------------------------------------------------------------
// Mobile menu toggle
// ---------------------------------------------------------------------
(function () {
  const toggle = document.getElementById("menu-toggle");
  const nav = document.querySelector(".main-nav");
  if (!toggle || !nav) return;
  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
})();

// ---------------------------------------------------------------------
// Hero background carousel (crossfade + Ken Burns zoom)
// ---------------------------------------------------------------------
(function () {
  const hero = document.getElementById("hero-carousel");
  if (!hero) return;
  const layers = Array.from(hero.querySelectorAll(".hero-bg-layer"));
  if (layers.length < 2) return;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion) return;

  let index = 0;
  setInterval(() => {
    layers[index].classList.remove("is-active");
    index = (index + 1) % layers.length;
    layers[index].classList.add("is-active");
  }, 7000);
})();

// ---------------------------------------------------------------------
// Animated count-up for the stats strip, triggered on scroll into view
// ---------------------------------------------------------------------
(function () {
  const numbers = document.querySelectorAll(".stat-number[data-count]");
  if (numbers.length === 0) return;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function animateCount(el) {
    const target = parseInt(el.dataset.count, 10) || 0;
    const suffixEl = el.querySelector(".suffix");
    const suffixHTML = suffixEl ? suffixEl.outerHTML : "";
    if (reduceMotion) {
      el.innerHTML = target + suffixHTML;
      return;
    }
    const duration = 1400;
    const start = performance.now();
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(target * eased);
      el.innerHTML = value + suffixHTML;
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  if (!("IntersectionObserver" in window)) {
    numbers.forEach(animateCount);
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 }
  );
  numbers.forEach((el) => observer.observe(el));
})();
