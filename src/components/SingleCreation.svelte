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
    
    let imgArray = []

    $: genImgUrl = generationResultDict['imgUrl'];
    $: genVideoUrl = generationResultDict['videoUrl'];


    let generationParams = {
            imageGeneration: true,
            videoGeneration: true,
            prompt: prompt,
            model: selectedModel.value,
            numIterations: numIterations[0],
            imgArray: imgArray,
        };
    
    $: if(numIterations){
        generationParams['numIterations'] = numIterations[0]
    }

    $: if (prompt){ generationParams['prompt'] = prompt }
    $: if (imgArray){ generationParams['imgArray'] = imgArray }

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
                    imgArray = [e.target.result]
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
    {#if imgArray.length == 0}
        <FileUpload on:input={handleImgUpload}>
            <img class="upload hover" src="/upload.png" alt="" />
        </FileUpload>
    {/if}

    {#each imgArray as img}
        <img class="avatar" src={img} alt="d" />
        <button
            class="hover"
            on:click={() => imgArray = []}
            style="background-color:white;">✖️</button
        >
    {/each}
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