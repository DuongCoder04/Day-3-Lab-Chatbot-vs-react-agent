import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.local_provider import LocalProvider


CPU_INCOMPATIBLE = False


def check_cpu_compatibility(model_path):
    global CPU_INCOMPATIBLE
    try:
        provider = LocalProvider(model_path=model_path)
        provider.generate("test")
        return True
    except OSError as e:
        if "0xc000001d" in str(e):
            CPU_INCOMPATIBLE = True
            return False
        raise


def test_generate():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    print("=== Test 1: generate() - non-streaming ===")
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        return False
    if CPU_INCOMPATIBLE:
        print(f"SKIPPED - CPU not compatible with this build")
        return None

    provider = LocalProvider(model_path=model_path)
    result = provider.generate("What is 2+2?")
    assert "content" in result
    assert "usage" in result
    assert "latency_ms" in result
    assert result["provider"] == "local"
    assert len(result["content"]) > 0
    print(f"Response: {result['content']}")
    print(f"Tokens: {result['usage']}")
    print(f"Latency: {result['latency_ms']}ms")
    print("PASSED\n")
    return True


def test_generate_with_system_prompt():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    print("=== Test 2: generate() with system prompt ===")
    if CPU_INCOMPATIBLE:
        print(f"SKIPPED - CPU not compatible with this build")
        return None
    provider = LocalProvider(model_path=model_path)
    result = provider.generate(
        "What is Python?",
        system_prompt="You are a helpful teacher. Answer in exactly 2 sentences."
    )
    assert "content" in result
    print(f"Response: {result['content']}")
    print(f"Tokens: {result['usage']}")
    print("PASSED\n")
    return True


def test_stream():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    print("=== Test 3: stream() - streaming ===")
    if CPU_INCOMPATIBLE:
        print(f"SKIPPED - CPU not compatible with this build")
        return None
    provider = LocalProvider(model_path=model_path)
    chunks = []
    for chunk in provider.stream("Say hello world"):
        chunks.append(chunk)
    output = "".join(chunks)
    assert len(output) > 0
    print(f"Streamed output: {output}")
    print(f"Total chunks: {len(chunks)}")
    print("PASSED\n")
    return True


def test_stream_with_system_prompt():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    print("=== Test 4: stream() with system prompt ===")
    if CPU_INCOMPATIBLE:
        print(f"SKIPPED - CPU not compatible with this build")
        return None
    provider = LocalProvider(model_path=model_path)
    chunks = []
    for chunk in provider.stream(
        "Tell me a fun fact.",
        system_prompt="You are a funny assistant."
    ):
        chunks.append(chunk)
    output = "".join(chunks)
    assert len(output) > 0
    print(f"Streamed output: {output}")
    print("PASSED\n")
    return True


def test_latency_measurement():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    print("=== Test 5: Latency measurement ===")
    if CPU_INCOMPATIBLE:
        print(f"SKIPPED - CPU not compatible with this build")
        return None
    provider = LocalProvider(model_path=model_path)
    start = time.time()
    result = provider.generate("What is the capital of France?")
    elapsed = time.time() - start
    actual_ms = int(elapsed * 1000)
    assert abs(result["latency_ms"] - actual_ms) < 2000
    print(f"Reported latency: {result['latency_ms']}ms")
    print(f"Actual elapsed: {actual_ms}ms")
    print("PASSED\n")
    return True


def test_multiple_calls():
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    print("=== Test 6: Multiple sequential calls ===")
    if CPU_INCOMPATIBLE:
        print(f"SKIPPED - CPU not compatible with this build")
        return None
    provider = LocalProvider(model_path=model_path)
    prompts = ["What is AI?", "What is ML?", "What is Deep Learning?"]
    for i, prompt in enumerate(prompts, 1):
        result = provider.generate(prompt)
        print(f"Call {i}: {len(result['content'])} chars, {result['latency_ms']}ms")
    print("PASSED\n")
    return True


def test_invalid_model_path():
    print("=== Test 7: Error handling - invalid model path ===")
    try:
        LocalProvider(model_path="./models/nonexistent.gguf")
        print("FAILED - should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"Correctly raised error: {e}")
        print("PASSED\n")
        return True


if __name__ == "__main__":
    load_dotenv()
    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")

    if os.path.exists(model_path):
        check_cpu_compatibility(model_path)
        if CPU_INCOMPATIBLE:
            print("=" * 60)
            print("CPU compatibility issue detected (error 0xc000001d).")
            print("The pre-built llama-cpp-python DLL was compiled for")
            print("a newer CPU (likely AVX-512). Your CPU (Ryzen 5825U)")
            print("does not support these instructions.")
            print()
            print("Solutions:")
            print("  1. Rebuild llama-cpp-python from source with:")
            print("     CMAKE_ARGS=\"-DGGML_NATIVE=OFF\" pip install llama-cpp-python")
            print("  2. Use a cloud LLM provider (OpenAI/Gemini)")
            print("  3. Install Visual Studio Build Tools + CMake, then retry")
            print("=" * 60)
            print()

    tests = [
        test_generate,
        test_generate_with_system_prompt,
        test_stream,
        test_stream_with_system_prompt,
        test_latency_measurement,
        test_multiple_calls,
        test_invalid_model_path,
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            result = test()
            if result is None:
                skipped += 1
            elif result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FAILED with exception: {e}\n")
            failed += 1

    total = len(tests)
    print(f"=== Results: {passed}/{total} passed, {failed} failed, {skipped} skipped ===")
