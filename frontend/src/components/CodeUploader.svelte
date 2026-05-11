<script>
    export let robotId;   // "A" o "B"
    export let color;     // para distinguir visualmente

    let status = "idle";  // idle | loading | ok | error
    let message = "";

    async function handleFile(event) {
        const file = event.target.files[0];
        if (!file) return;

        status = "loading";
        message = "";

        const formData = new FormData();
        formData.append("file", file);

        try {
        const res = await fetch(`http://localhost:8000/robot/${robotId}/code`, {
            method: "POST",
            body: formData,
        });

        const json = await res.json();

        if (res.ok) {
            status = "ok";
            message = `✓ Código cargado para Robot ${robotId}`;
        } else {
            status = "error";
            message = `✗ ${json.detail}`;
        }
        } catch (e) {
        status = "error";
        message = "✗ No se pudo conectar con el servidor";
        }
    }
    </script>

    <div class="uploader" style="--accent: {color}">
        <h3>Robot {robotId}</h3>
        <label class="btn">
            Subir código (.py)
            <input type="file" accept=".py" on:change={handleFile} hidden />
        </label>
        {#if status === "loading"}
            <p class="msg loading">Cargando...</p>
        {:else if status === "ok"}
            <p class="msg ok">{message}</p>
        {:else if status === "error"}
            <p class="msg error">{message}</p>
        {/if}
    </div>

    <style>
    .uploader {
        border: 2px solid var(--accent);
        border-radius: 8px;
        padding: 1rem;
        min-width: 200px;
        text-align: center;
    }
    h3 { margin: 0 0 0.75rem; color: var(--accent); }
    .btn {
        display: inline-block;
        padding: 0.5em 1.2em;
        background: var(--accent);
        color: white;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
    }
    .msg { margin-top: 0.5rem; font-size: 0.9em; }
    .ok    { color: #4caf50; }
    .error { color: #f44336; }
    .loading { color: #aaa; }
</style>