<script>
    export let imgUrl = ''
    export let videoUrl = ''
</script>

{#if imgUrl != ''}
    <div class="centered">
        <h2>Generated Image</h2>
    </div>
    <div style="margin-bottom:40px" class="centered">
        <img
            style="margin-top: 20px"
            src={imgUrl}
            alt="Generated Image"
            width="50%"
        />
    </div>
{/if}

{#if videoUrl != ''}
    <div class="centered">
        <h2>Generated Video</h2>
    </div>
    <div style="margin-bottom:40px" class="centered">
        <video width="50%" controls>
            <source 
                src={videoUrl} 
                type="video/mp4" 
            />
            Your browser does not support mp4...
        </video>
    </div>
{/if}

<style>
    .centered {
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>