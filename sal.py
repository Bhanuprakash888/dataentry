def get_url_nav_ui(driver, url, logger, sctask_number):
    try:
        # Navigate to the URL
        driver.get(url)
        logger.info(f"Navigated to: {url}")
        
        # Wait for the page to load
        wait_90 = WebDriverWait(driver, 90)
        wait_90.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(2)
        logger.info("Opened webpage")

        # Access the first shadow host
        shadow_host = driver.find_element(By.XPATH, "//macroponent-f51912f4c700201072b211d4d8c26010[@app-id='a84adaf4c700201072b211d4d8c260b7']")
        time.sleep(4)
        logger.info(f"Found shadow host: {shadow_host}")

        # Traverse through the shadow DOM layers
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', shadow_host)
        logger.info(f"1st Shadow root accessed.")

        # Traverse subsequent shadow roots based on their respective XPaths or CSS selectors
        shadow_root_2 = shadow_root.find_element(By.CSS_SELECTOR, 'sn-canvas-appshell-root').shadow_root
        logger.info(f"2nd Shadow root accessed.")
        
        shadow_root_3 = shadow_root_2.find_element(By.CSS_SELECTOR, 'sn-canvas-appshell-layout').shadow_root
        logger.info(f"3rd Shadow root accessed.")
        
        shadow_root_4 = shadow_root_3.find_element(By.CSS_SELECTOR, 'sn-polaris-layout').shadow_root
        logger.info(f"4th Shadow root accessed.")

        shadow_root_5 = shadow_root_4.find_element(By.XPATH, './div[2]/div[2]/div[1]/sn-polaris-header').shadow_root
        logger.info(f"5th Shadow root accessed.")

        shadow_root_6 = shadow_root_5.find_element(By.CSS_SELECTOR, 'nav div div[3] div[1] div[1] div sn-search-input-wrapper').shadow_root
        logger.info(f"6th Shadow root accessed.")

        shadow_root_7 = shadow_root_6.find_element(By.CSS_SELECTOR, 'sn-component-workspace-global-search-typeahead').shadow_root
        logger.info(f"7th Shadow root accessed.")

        # Locate the input element inside the 7th shadow root
        input_element = shadow_root_7.find_element(By.XPATH, './div/div[1]/div/div/input')
        logger.info("Found input element inside the 7th shadow root.")

        # Pass the SCTASK number to the input field
        input_element.send_keys(sctask_number)
        logger.info(f"Entered SCTASK number: {sctask_number}")

        # Press Enter to search
        input_element.send_keys(Keys.RETURN)
        logger.info("Pressed Enter.")

        return input_element  # You can return the element if needed for further actions.

    except Exception as e:
        logger.error(f"Error encountered: {str(e)}")
        raise