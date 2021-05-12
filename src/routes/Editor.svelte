<script>
  import Select from 'svelte-select';

  let modelArray = [
    {value: 'dreamy', label: '✨ Dreamy', possibilities:'anything you want'},
    {value: 'faces', label: '😗 Faces', possibilities: 'faces'},
  ];

  let selectedModel = modelArray[0]

  let singleCreationActive = false
  let collaborationActive = false

  let generationConfig = {
      imageGeneration: false,
      videoGeneration: false,
  }

  let generationReady = false

  let promptPlaceholderArray = [
      "The moustache of Salvador Dali",
      "CHANEL alien collection",
      "Birds wearing CHANEL",
      "Roses made of CHANEL",
      "CHANEL exotic jewelry collection",
      "Flowers made of diamonds",
    ]
  let prompt = ""


  function handleSelect(event) {
    selectedModel = event.detail
  }

  function activateSingleCreation(){
      singleCreationActive = !singleCreationActive
      collaborationActive = false

  }
  function activateCollaboration(){
      collaborationActive = !collaborationActive
      singleCreationActive = false

  }
  function updateGenerationState(){

      for (var key in generationConfig){
        console.log(key)
        console.log(generationConfig[key])
        
        if(generationConfig[key]){
            generationReady = true
            return
        }
      }

      generationReady = false
}

</script>
<h1>🥸 Bigotis Editor</h1>
<h3>Select a style</h3>
<Select items={modelArray} selectedValue={selectedModel} on:select={handleSelect}></Select>

<h3>Select a mode</h3>
<div class="btn-container">
    <button on:click={activateSingleCreation}>Single Creation</button>
    <button on:click={activateCollaboration}>Colaboration</button>
</div>

{#if singleCreationActive}
    <h3>
        What do you want to generate?
    </h3>
    <div class="input-container">
        <input bind:value={prompt} placeholder={promptPlaceholderArray[Math.floor(Math.random() * promptPlaceholderArray.length)]}>
    </div>        

    {#if prompt != ""}
        <div class="label-container">
            <label>
                <input 
                    type=checkbox 
                    bind:checked={generationConfig['imageGeneration']} 
                    on:click={() => window.setTimeout(updateGenerationState, 0)}
                >
                Image Generation
            </label>
            <label>
                <input 
                    type=checkbox 
                    bind:checked={generationConfig['videoGeneration']} 
                    on:click={() => window.setTimeout(updateGenerationState, 0)}
                >
                Video Generation
            </label>

            {#if generationReady}
                <div class=btn-container style="margin-top: 20px">
                    <button>Generate</button>
                </div>
            {/if}
        </div>
    {/if}

{:else if collaborationActive}
    Collaboration
{/if}

<style>
    .input-container input{
        width:100%;
        height: 50px;

    }
    .label-container {
        margin-top: 20px;
    }
</style>