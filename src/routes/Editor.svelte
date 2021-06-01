<script>
    import Select from "svelte-select";
    import SingleCreation from "../components/SingleCreation.svelte"
    import StoryMode from "../components/StoryMode.svelte"
    
    let activeMode = ''

    let modelArray = [
        {
            value: "dalle",
            label: "🌴 DALL-E",
            possibilities: "faces",
        },
        {
            value: "taming",
            label: "🌎 Taming",
            possibilities: "faces",
        },
        {
            value: "aphantasia",
            label: "✨ Aphantasia",
            possibilities: "anything you want",
        },
        {
            value: "stylegan",
            label: "😗 StyleGAN",
            possibilities: "faces",
        },
    ];
   
    let selectedModel = modelArray[1];

    function handleSelect(event) {
        selectedModel = event.detail;
    }

</script>
<h1>🥸 Bigotis Editor</h1>
<h3>Select a style</h3>
<Select
    items={modelArray}
    bind:selectedValue={selectedModel}
    on:select={handleSelect}
/>

<h3>Select a mode</h3>
<div class="btn-container">
    <button on:click={()=>activeMode='singleCreation'}>Single Creation</button>
    <button on:click={()=>activeMode='storyMode'}>Story Mode</button>
</div>

{#if activeMode=='singleCreation'}
    <SingleCreation selectedModel={selectedModel}/>
{:else if activeMode=='storyMode'}
    <StoryMode selectedModel={selectedModel}/>
{/if}

<style>
</style>
