<script>
    import ModelParams from "./ModelParams.svelte"
    import Generate from "./Generate.svelte"
    import {promptPlaceholderArray} from "../utils.ts"
    import Slider from "@bulatdashiev/svelte-slider";

    export let selectedModel

    let numIterations
    let selectedResolution

    let promptArray = ['']
    let durationArray = [[0.5]]

    let minDuration = 0.1
    let maxDuration = 10


    function addPrompt(){
        promptArray.push('')
        durationArray.push([0.5])
        promptArray = promptArray
        durationArray = durationArray
    }

</script>

{#each promptArray as _, idx}
    <div class="input-container">
        <input
            bind:value={promptArray[idx]}
            placeholder={promptPlaceholderArray[
                Math.floor(Math.random() * promptPlaceholderArray.length)
            ]}
        />
        
        <h3>Duration {durationArray[idx][0]}</h3>
        <Slider
            bind:value={durationArray[idx]}
            min={minDuration}
            max={maxDuration}
            step="0.1"
        />

    </div>
{/each}

<button on:click={addPrompt}> Add prompt </button>

<ModelParams
    selectedModel={selectedModel}
    bind:numIterations={numIterations}
    bind:selectedResolution={selectedResolution}
/>

<Generate />


<style>
    .input-container {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .input-container input {
        width: 100%;
        height: 50px;
        margin-right: 20px;
    }
    .label-container {
        margin-top: 20px;
    }

</style>