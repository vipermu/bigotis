import os
import yaml
import math
import glob
from typing import *

import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import torch.nn.functional as F
from PIL import Image
import numpy as np
import clip
from omegaconf import OmegaConf

# from cmodels.taming.vqgan import VQModel
from models.taming.vqgan import VQModel


# TODO: put this func into a utils file or something
def get_stacked_random_crops(img, num_random_crops=64):
    img_size = [img.shape[2], img.shape[3]]

    crop_list = []
    for _ in range(num_random_crops):
        crop_size_y = int(img_size[0] * torch.zeros(1, ).uniform_(.75, .95))
        crop_size_x = int(img_size[1] * torch.zeros(1, ).uniform_(.75, .95))

        y_offset = torch.randint(0, img_size[0] - crop_size_y, ())
        x_offset = torch.randint(0, img_size[1] - crop_size_x, ())

        crop = img[:, :, y_offset:y_offset + crop_size_y,
                   x_offset:x_offset + crop_size_x]

        crop = F.upsample_bilinear(crop, (224, 224))

        crop_list.append(crop)

    img = torch.cat(crop_list, axis=0)

    return img


class TamingDecoder:
    def __init__(self, ):
        if not os.path.exists('./server/models/taming/last.ckpt'):
            os.system(
                " wget 'https://heibox.uni-heidelberg.de/f/867b05fc8c4841768640/?dl=1' -O 'server/models/taming/last.ckpt'"
            )

        if not os.path.exists('./server/models/taming/model.yaml'):
            os.system(
                "wget 'https://heibox.uni-heidelberg.de/f/274fb24ed38341bfa753/?dl=1' -O 'server/models/taming/model.yaml'"
            )

        self.target_img_size = 512
        self.embed_size = self.target_img_size // 16

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("USING ", self.device)

        self.clip_model, self.clip_preprocess = clip.load(
            "ViT-B/32",
            device=self.device,
        )
        self.clip_model.eval()
        # NOTE: just adding the normalization transformation
        self.clip_transform = T.Compose([
            self.clip_preprocess.transforms[4],
        ])

        self.norm_trans = T.Normalize(
            (0.48145466, 0.4578275, 0.40821073),
            (0.26862954, 0.26130258, 0.27577711),
        )

        config_xl = self.load_config(
            "server/models/taming/model.yaml",
            display=False,
        )
        self.vqgan_model = self.load_vqgan(
            config_xl,
            ckpt_path="server/models.taming/last.ckpt",
        ).to(self.device)
        
        self.aug_transform = torch.nn.Sequential(
            T.RandomHorizontalFlip(),
            T.RandomAffine(24, (.1, .1)),
        ).cuda()

    def augment(self, into, cutn=20): #into: 1x3x400x688
        crop_scaler = 1
        #pdb.set_trace()
        into = torch.nn.functional.pad(into, (self.target_img_size//2, self.target_img_size//2, self.target_img_size//2, self.target_img_size//2), mode='constant', value=0)
        #into: 1 x 3 x 800 x 1088

        into = self.aug_transform(into) #RandomHorizontalFlip and RandomAffine

        p_s = []
        for ch in range(cutn):
            size = int(torch.normal(1.2, .3, ()).clip(.43, 1.9) * self.target_img_size) #433
            
            if ch > cutn - 4:
                size = int(self.target_img_size*1.4)

            offsetx = torch.randint(0, int(self.target_img_size*2 - size), ())
            offsety = torch.randint(0, int(self.target_img_size*2 - size), ())
            apper = into[:, :, offsetx:offsetx + size, offsety:offsety + size]
            apper = torch.nn.functional.interpolate(apper, (int(224*crop_scaler), int(224*crop_scaler)), mode='bilinear', align_corners=True)
            p_s.append(apper)
        into = torch.cat(p_s, 0)

        up_noise = 0.11
        into = into + up_noise*torch.rand((into.shape[0], 1, 1, 1)).cuda()*torch.randn_like(into, requires_grad=False)

        return into

    def vqgan_preprocess(
        self,
        img,
    ):
        img = img.convert("RGB")

        min_img_dim = min(img.size)

        scale_factor = self.target_img_size / min_img_dim
        scaled_img_dim = (round(scale_factor * img.size[0]),
                        round(scale_factor * img.size[1]))
        img = img.resize(scaled_img_dim, Image.LANCZOS)
        img = TF.center_crop(img, output_size=2 * [self.target_img_size])
        img_tensor = torch.unsqueeze(T.ToTensor()(img), 0).to(self.device)

        img_tensor = 2. * img_tensor - 1.

        return img_tensor
    
    @staticmethod
    def load_config(config_path, display=False):
        config = OmegaConf.load(config_path)

        if display:
            print(yaml.dump(OmegaConf.to_container(config)))

        return config

    @staticmethod
    def load_vqgan(
        config,
        ckpt_path=None,
    ):
        model = VQModel(**config.model.params)

        ckpt_path = "server/models/taming/last.ckpt"
        if ckpt_path is not None:
            # XXX: check wtf is going on here
            sd = torch.load(ckpt_path, map_location="cpu")["state_dict"]
            missing, unexpected = model.load_state_dict(sd, strict=False)

        return model.eval()

    def get_clip_img_encodings(
        self,
        img_batch,
        do_preprocess=True,
    ):
        if do_preprocess:
            # img_batch = self.clip_transform(img_batch)
            img_batch = self.norm_trans(img_batch)
            img_batch = F.upsample_bilinear(img_batch, (224, 224))

        img_logits = self.clip_model.encode_image(img_batch)
        img_logits = img_logits / img_logits.norm(dim=-1, keepdim=True)

        return img_logits

    def compute_clip_loss(self, img, text):
        img_logits = self.get_clip_img_encodings(img)

        tokenized_text = clip.tokenize([text]).to(self.device).detach().clone()
        text_logits = self.clip_model.encode_text(tokenized_text)

        text_logits = text_logits / text_logits.norm(dim=-1, keepdim=True)

        loss = -torch.cosine_similarity(text_logits, img_logits).mean()

        return loss


    def generate_from_prompt(
        self,
        prompt: str,
        lr: float = 0.5,
        img_save_freq: int = 1,
        num_generations: int = 100,
        num_random_crops: int = 32,
        img_batch=None,
    ):
        batch_size = 1

        z_logits = .5 * torch.randn(
            batch_size,
            256,
            self.embed_size,
            self.embed_size,
        ).cuda()

        z_logits = torch.nn.Parameter(
            torch.sinh(1.9 * torch.arcsinh(z_logits)), )

        if img_batch is not None:
            clip_img_z_logits = self.get_clip_img_encodings(img_batch)
            clip_img_z_logits = clip_img_z_logits.detach().clone()

            z, _, [_, _, indices] = self.vqgan_model.encode(img_batch)

            z_logits = torch.nn.Parameter(z)
            img_z_logits = z.detach().clone()

        optimizer = torch.optim.AdamW(
            params=[z_logits],
            lr=lr,
            betas=(0.9, 0.999),
            weight_decay=0.1,
        )

        gen_img_list = []
        z_logits_list = []

        for step in range(num_generations):
            loss = 0
            
            if step % img_save_freq == 0:
                print("Adding logits...")
                z_logits_list.append(z_logits.detach().clone())

            z = self.vqgan_model.post_quant_conv(z_logits)
            x_rec = self.vqgan_model.decoder(z)
            x_rec = (x_rec.clip(-1, 1) + 1) / 2
            x_rec_stacked = self.augment(x_rec)

            # x_rec_stacked = get_stacked_random_crops(
            #     img=x_rec,
            #     num_random_crops=num_random_crops,
            # )

            loss += 10 * self.compute_clip_loss(x_rec_stacked, prompt)

            # if img_batch is not None:
            #     loss += -10 * torch.cosine_similarity(z_logits,
            #                                           img_z_logits).mean()
            # if img_batch is not None:
            #     loss += -10 * torch.cosine_similarity(
            #         self.get_clip_img_encodings(x_rec), clip_img_z_logits).mean()

            print(loss)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if step % img_save_freq == 0:
                print("Adding img...")
                x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
                gen_img_list.append(x_rec_img)

                x_rec_img.save(f"generations/{step}.png")

            torch.cuda.empty_cache()

        torch.save(z_logits, f'{prompt}_logits.pt')

        return gen_img_list, z_logits_list

    def interpolate(
        self,
        z_logits_list,
        duration_list,
    ):
        gen_img_list = []
        fps = 25

        for idx, (z_logits,
                  duration) in enumerate(zip(z_logits_list, duration_list)):
            num_steps = int(duration * fps)
            z_logits_1 = z_logits
            z_logits_2 = z_logits_list[(idx + 1) % len(z_logits_list)]

            for step in range(num_steps):
                weight = math.sin(1.5708 * step / num_steps)**2
                z_logits = weight * z_logits_2 + (1 - weight) * z_logits_1

                z = self.vqgan_model.post_quant_conv(z_logits)
                x_rec = self.vqgan_model.decoder(z)
                x_rec = (x_rec.clip(-1, 1) + 1) / 2

                x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
                gen_img_list.append(x_rec_img)

        return gen_img_list
    
    def generate_video_from_prompt(
        self,
        prompt: str,
        init_latent:torch.Tensor,
        lr: float = 0.3,
        num_generations: int = 1000,
        num_random_crops: int = 16,
        num_zoom_interp_steps=4,
        num_zoom_train_steps=4,
        zoom_offset = 16,
    ):
        z_logits = init_latent.detach().clone()
        z_logits = torch.nn.Parameter(z_logits)

        optimizer = torch.optim.AdamW(
            params=[z_logits],
            lr=lr,
            betas=(0.9, 0.999),
            weight_decay=0.1,
        )
                

        gen_img_list = []
        z_logits_list = []
        for step in range(num_generations):
            with torch.no_grad():

                z = self.vqgan_model.post_quant_conv(z_logits)
                x_rec = self.vqgan_model.decoder(z)
                x_rec = (x_rec.clip(-1, 1) + 1) / 2
                
                x_rec_size = x_rec.shape[-1]

                x_rec_zoom = x_rec[:, :, zoom_offset:-zoom_offset, zoom_offset:-zoom_offset]
                x_rec_zoom = torch.nn.functional.interpolate(x_rec_zoom, (x_rec_size, x_rec_size), mode="bilinear",)
                
                x_rec_zoom = 2. * x_rec_zoom - 1
                zoom_z_logits, _, [_, _, indices] = self.vqgan_model.encode(x_rec_zoom)
                
                z_logits.data = zoom_z_logits.clone().detach()

            for zoom_train_step in range(num_zoom_train_steps):
                loss = 0
                z = self.vqgan_model.post_quant_conv(z_logits)
                x_rec = self.vqgan_model.decoder(z)
                x_rec = (x_rec.clip(-1, 1) + 1) / 2
                x_rec_stacked = self.augment(x_rec,)

                loss += 10 * self.compute_clip_loss(x_rec_stacked, prompt)

                print(loss)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # print("Adding img...")
                # x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
                # x_rec_img.save(f"generations/{step}_{zoom_train_step}.jpg")
                
            z_logits_1 = init_latent
            z_logits_2= z_logits

            for zoom_step in range(num_zoom_interp_steps):
                weight = zoom_step/num_zoom_interp_steps
                interp_logits = weight * z_logits_2 + (1 - weight) * z_logits_1

                with torch.no_grad():
                    z = self.vqgan_model.post_quant_conv(interp_logits)
                    x_rec = self.vqgan_model.decoder(z)
                    x_rec = (x_rec.clip(-1, 1) + 1) / 2
                    
                print("Adding img...")
                x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
                gen_img_list.append(x_rec_img)

                x_rec_img.save(f"generations/{step}_{zoom_step}.jpg")

            init_latent = z_logits.detach().clone()

            torch.cuda.empty_cache()

        return gen_img_list, z_logits_list


if __name__ == '__main__':
    taming_decoder = TamingDecoder()

    img_tensor_list = []
    # for img_path in glob.glob("./img_refs/*"):
    #     img = Image.open(img_path)
    #     img_tensor_list.append(self.vqgan_preprocess(img))

    # img_path = "/home/vicc/Downloads/papagei2.jpg"
    # img = Image.open(img_path)
    # img_tensor_list.append(taming_decoder.vqgan_preprocess(img))

    # img = torch.cat(img_tensor_list)

    img = None

    # img = Image.open('ref_imgs/1.png')
    # img = dalle_img_preprocess(img)
    prompt='Creepy Disney ghosts dancing in the fire'

    # gen_img_list, z_logits_list = taming_decoder.generate_from_prompt(
    #     prompt=prompt,
    #     img_batch=img,
    #     lr=0.5,
    #     num_generations=200,
    # )
    
    # torch.cuda.empty_cache()
    
    init_latent_path = f"./{prompt}_logits.pt"
    init_latent = torch.load(init_latent_path).to('cuda')
    gen_img_list, z_logits_list = taming_decoder.generate_video_from_prompt(
        prompt=prompt,
        init_latent=init_latent,
        lr=0.2,
    )
    gen_img_list = taming_decoder.interpolate(z_logits_list, [2])# 
