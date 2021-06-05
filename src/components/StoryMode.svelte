<script>
    import FileUpload from 'sveltefileuploadcomponent';
    import ModelParams from "./ModelParams.svelte"
    import Generate from "./Generate.svelte"
    import DisplayGeneration from "./DisplayGeneration.svelte"
    import {promptPlaceholderArray} from "../utils.ts"
    import Slider from "@bulatdashiev/svelte-slider";

    export let selectedModel

    let numIterations = [200]
    let selectedResolution = [720, 1280]
    
    $: if(numIterations){
        generationParams['numIterations'] = numIterations[0]
    }

    let promptArray = ['']
    let durationArray = [[1.5]]
    let condImgArray = []

    let minDuration = 0.5
    let maxDuration = 10
    
    let generationParams = {
        storyGeneration: true,
        model: selectedModel.value,
        numIterations: numIterations[0],
        promptArray:promptArray,
        durationArray:durationArray,
        condImgArray:condImgArray,
    };
    
    let generationResultDict = {
        'imgUrl': '',
        'videoUrl': '',
    }
    
    $: genImgUrl = generationResultDict['imgUrl'];
    $: genVideoUrl = generationResultDict['videoUrl'];
    
    $: if (selectedModel.value == "aphantasia") {
        generationParams[
            "resolution"
        ] = `${selectedResolution[0]}-${selectedResolution[1]}`;
    }


    function addPrompt(){
        promptArray.push('')
        durationArray.push([durationArray[durationArray.length-1]])
        condImgArray.push(undefined)
        promptArray = promptArray
        durationArray = durationArray
        condImgArray = condImgArray
    }
    
    function handleImgUpload(event, idx) {
        const files = event.detail.files
        if (files.length > 1){
            alert("Only handling one image for now")
        } else {
            files.forEach((file) => {
                let reader = new FileReader()
                reader.readAsDataURL(file)
                reader.onload = (e) => {
                    condImgArray[idx] = e.target.result
                }
            })
        }
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
        {#if typeof condImgArray[idx] == "undefined"}
            <FileUpload on:input={(e) => handleImgUpload(e, idx)}>
                <img class="upload hover" src="/upload.png" alt="" />
            </FileUpload>
        {:else}
            <img class="avatar" src={condImgArray[idx]} alt="d" />
            <button
                class="hover"
                on:click={() => condImgArray[idx] = undefined}
                style="background-color:white;">✖️</button
            >
        {/if}

        <h3 style="margin-left: 20pt;">Duration {durationArray[idx][0]}</h3>
        <Slider
            bind:value={durationArray[idx]}
            min={minDuration}
            max={maxDuration}
            step="0.10"
        />

    </div>
{/each}

<button on:click={addPrompt}> Add prompt </button>

<ModelParams
    bind:selectedModel={selectedModel}
    bind:numIterations={numIterations}
    bind:selectedResolution={selectedResolution}
/>

<Generate 
    bind:generationParams={generationParams}
    bind:generationResultDict={generationResultDict}
/>

<DisplayGeneration
    bind:imgUrl={genImgUrl}
    bind:videoUrl={genVideoUrl}
/>


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
    
    .hover:hover {
        opacity: 0.5;
    }

    .upload {
        display: flex;
        height: 30pt;
        width: 30pt;
        cursor: pointer;
        margin-right: 20px;
    }
    .avatar {
        display: flex;
        height: 200px;
        width: 200px;
    }

</style>