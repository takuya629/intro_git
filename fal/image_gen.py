import fal_client
import os
import urllib.request

def generate_image(prompt: str, model: str = "fal-ai/flux/schnell", output_file: str = "output.png"):
    print(f"生成中: {prompt}")
    print(f"モデル: {model}")

    result = fal_client.run(
        model,
        arguments={
            "prompt": prompt,
            "image_size": "landscape_4_3",
            "num_inference_steps": 4,
            "num_images": 1,
        }
    )

    images = result.get("images", [])
    if not images:
        print("画像が生成されませんでした")
        return

    url = images[0]["url"]
    print(f"生成完了: {url}")

    urllib.request.urlretrieve(url, output_file)
    print(f"保存完了: {output_file}")
    return output_file


if __name__ == "__main__":
    prompt = "A serene Japanese garden with cherry blossoms, koi pond, and wooden bridge, photorealistic"
    generate_image(prompt, output_file="output.png")
