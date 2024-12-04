import asyncio

from CaptchaSolver import CaptchaSolver


async def main():
    # proxy = ''
    solver = CaptchaSolver(CAPTCHA_SOLVER_CLIENT_API_KEY)
    captcha_key = None

    try:
        task_id = await solver.create_task_for_captcha()

        print(f"Task ID: {task_id}")

        captcha_key = await solver.get_captcha_key(task_id)

        print(f"Captcha Key: {captcha_key}")

    except Exception as error:
        print(f'Error while processing captcha! {error}')

    try:
        await solver.make_request_to_claim(captcha_key, claim_address)
    except Exception as error:
        print(f'Error while processing claimed! {error}')

    await solver.session.close()

# USE_PROXY = True
CAPTCHA_SOLVER_CLIENT_API_KEY = ''
claim_address = ''
asyncio.run(main())
