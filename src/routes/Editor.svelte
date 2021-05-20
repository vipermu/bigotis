<script>
    import Select from "svelte-select";
    import SingleCreation from "../components/SingleCreation.svelte"
    import StoryMode from "../components/StoryMode.svelte"
    
    let activeMode = ''

    let modelArray = [
        {
            value: "dalle",
            label: "🌴 Wild",
            possibilities: "faces",
        },
        {
            value: "aphantasia",
            label: "✨ Dreamy",
            possibilities: "anything you want",
        },
        {
            value: "stylegan",
            label: "😗 Faces",
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
    <button on:click={()=>activeMode='collaboration'}>Colaboration</button>
</div>

{#if activeMode=='singleCreation'}
    <SingleCreation selectedModel={selectedModel}/>
{:else if activeMode=='storyMode'}
    <StoryMode selectedModel={selectedModel}/>
{:else if activeMode=='collaboration'}
    Collaboration
{/if}

<style>
</style>
