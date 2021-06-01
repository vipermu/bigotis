<script>
    import { Jumper } from "svelte-loading-spinners";
    import {serverIP, apiPort} from "../utils.ts"
        
    export let generationParams
    export let generationResultDict
    
    let generatingImage = false;

    async function generate() {
        console.log("GENERATING WITH PARAMS", generationParams);
        generatingImage = true;

        const serverURL = `http://${serverIP}:${apiPort}`

        let fetchURL = new URL(`${serverURL}/generate`);
        fetchURL.search = new URLSearchParams(generationParams).toString();

        console.log("FETCHING DATA");
        const res = await fetch(fetchURL.toString(), {
            method: "GET",
        });

        generationResultDict = await res.json();
        console.log("RESULTS", generationResultDict);

        generatingImage = false;
    }
</script>

{#if !generatingImage}
    <div class="btn-container" style="margin-top: 20px">
        <button on:click={generate}>Generate</button>
    </div>
{:else}
    <div style="margin-top: 10px">
        <Jumper
            size="60"
            color="#BE3CC6"
            unit="px"
            duration="1.3s"
        />
    </div>
{/if}