<script>
    import FileUpload from 'sveltefileuploadcomponent';
    import ModelParams from "./ModelParams.svelte"
    import {promptPlaceholderArray} from "../utils.ts"
    import Generate from "./Generate.svelte"
    import DisplayGeneration from "./DisplayGeneration.svelte"

    export let selectedModel
 
    let numIterations = [50];
    let selectedResolution = [1024, 1024];

    let prompt = "";
    let generationResultDict = {
        'imgUrl': '',
        'videoUrl': '',
    }
    
    let condImg

    $: genImgUrl = generationResultDict['imgUrl'];
    $: genVideoUrl = generationResultDict['videoUrl'];


    let generationParams = {
            imageGeneration: true,
            videoGeneration: true,
            prompt: prompt,
            model: selectedModel.value,
            numIterations: numIterations[0],
            condImg: condImg,
        };
    
    $: if(numIterations){
        generationParams['numIterations'] = numIterations[0]
    }

    $: if (prompt){ generationParams['prompt'] = prompt }
    $: if (condImg){ generationParams['condImg'] = condImg }

    $: generationReady = generationParams['imageGeneration'] || generationParams['videoGeneration'];
    
    $: if (selectedModel.value == "aphantasia") {
        generationParams[
            "resolution"
        ] = `${selectedResolution[0]}-${selectedResolution[1]}`;
    }

    function updateGenerationState(generationKey) {
        generationParams[generationKey] = !generationParams[generationKey]
    }

    function handleImgUpload(event) {
        const files = event.detail.files
        if (files.length > 1){
            alert("Only handling one image for now")
        } else {
            files.forEach((file) => {
                let reader = new FileReader()
                reader.readAsDataURL(file)
                reader.onload = (e) => {
                    condImg = e.target.result
                }
            })
        }
    }

</script>
<h3>What do you want to generate?</h3>
<div class="input-container">
    <input
        bind:value={prompt}
        placeholder={promptPlaceholderArray[
            Math.floor(Math.random() * promptPlaceholderArray.length)
        ]}
    />
</div>

{#if selectedModel.value == 'taming'}
    <h3>
        You can condition your Generation with an image:
    </h3>
    {#if typeof condImg == "undefined"}
        <FileUpload on:input={handleImgUpload}>
            <img class="upload hover" src="/upload.png" alt="" />
        </FileUpload>
    {:else}
        <img class="avatar" src={condImg} alt="d" />
        <button
            class="hover"
            on:click={() => condImg = undefined}
            style="background-color:white;">✖️</button
        >
    {/if}

{/if}

{#if prompt != ""}
    <div class="label-container">
        <label>
            <h3>
                <input
                    type="checkbox"
                    bind:checked={generationParams["imageGeneration"]}
                    on:click={() => updateGenerationState('imageGeneration')}
                />

                Image Generation
            </h3>
        </label>
        <label>
            <h3>
                <input
                    type="checkbox"
                    bind:checked={generationParams["videoGeneration"]}
                    on:click={() => updateGenerationState('videoGeneration')}
                />
                Video Generation
            </h3>
        </label>

        <ModelParams
            bind:selectedModel={selectedModel}
            bind:numIterations={numIterations}
            bind:selectedResolution={selectedResolution}
        />

        {#if generationReady}
            <Generate 
                bind:generationParams={generationParams}
                bind:generationResultDict={generationResultDict}
            />
        {/if}
    </div>
    
    <DisplayGeneration
        bind:imgUrl={genImgUrl}
        bind:videoUrl={genVideoUrl}
    />

{/if}

<style>
    .input-container input {
        width: 100%;
        height: 50px;
    }
    .label-container {
        margin-top: 20px;
    }
    .centered {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .hover:hover {
        opacity: 0.5;
    }

    .upload {
        display: flex;
        height: 30pt;
        width: 30pt;
        cursor: pointer;
    }
    .avatar {
        display: flex;
        height: 200px;
        width: 200px;
    }

</style>